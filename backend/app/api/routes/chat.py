import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging_config import logger
from app.core.llm import (
    get_llm_provider,
    LLMConfigurationError,
    LLMConnectionError,
    LLMAuthenticationError,
    LLMModelNotFoundError,
    LLMTimeoutError,
    LLMProviderError,
)
from app.core.embeddings import get_embedding_provider, EmbeddingProviderError
from app.retrieval.service import RetrievalService, RetrievedChunk
from app.database.connection import get_db
from app.database.session_service import SessionService
from app.schemas.chat import ChatRequest, ChatResponse, ArtifactMetadata

router = APIRouter(tags=["Chat"])

DEFAULT_BASE_PROMPT = (
    "You are The Lenny Growth Assistant, a strategic AI copilot for Product Managers, "
    "Growth Leaders, and Founders, inspired by Lenny's Podcast and Newsletter."
)


def detect_artifact_intent(message: str) -> Optional[Dict[str, str]]:
    """
    Detects whether the user query requests an artifact (essay, document, strategy guide, or interactive tool).
    Returns dictionary with artifact metadata if intent detected, else None.
    """
    msg = message.lower().strip()

    # 1. Ship 30 / Atomic Essay requests
    if any(k in msg for k in ("essay", "ship 30", "atomic essay")):
        return {"type": "essay", "category": "Ship 30 Atomic Essay"}

    # 2. Interactive HTML tool requests
    if any(k in msg for k in ("html dashboard", "html widget", "html calculator", "interactive dashboard", "interactive calculator")):
        return {"type": "html", "category": "Interactive Tool"}

    # 3. Strategy Guide / Playbook / Memo / Document / Explicit Artifact requests
    if any(k in msg for k in (
        "as an artifact",
        "create an artifact",
        "generate an artifact",
        "make an artifact",
        "strategy guide",
        "audit playbook",
        "growth playbook",
        "product playbook",
        "strategy memo",
        "framework document",
    )):
        return {"type": "markdown", "category": "Strategy Guide"}

    return None


def extract_artifact_title(content: str, fallback_topic: str) -> str:
    """
    Extracts a clean title from the first markdown # Heading, or falls back to query topic.
    """
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("# "):
            title = line.lstrip("#").strip()
            title = title.replace("**", "").replace("*", "").replace("`", "")
            if len(title) >= 3:
                return title[:200]

    # Fallback to query topic
    clean = fallback_topic.strip().rstrip(".?!")
    for prefix in (
        "write an essay on ",
        "write an essay about ",
        "draft an essay on ",
        "draft an essay about ",
        "create an artifact for ",
        "create an artifact on ",
        "generate an artifact for ",
        "generate an artifact on ",
        "generate a strategy guide on ",
        "generate a strategy guide for ",
        "write a strategy guide on ",
        "write a strategy guide for ",
    ):
        if clean.lower().startswith(prefix):
            clean = clean[len(prefix):]
            break

    title = clean.strip()
    return title.capitalize()[:200] if title else "Strategic Growth Artifact"


def build_rag_system_prompt(
    retrieved_chunks: List[RetrievedChunk],
    database_has_transcripts: bool,
    artifact_intent: Optional[Dict[str, str]] = None,
) -> str:
    """
    Constructs an explicit system prompt with verified transcript context and strict grounding guidelines.
    """
    artifact_instruction = ""
    if artifact_intent:
        art_type = artifact_intent.get("type", "markdown")
        if art_type == "essay":
            artifact_instruction = (
                "\n\nDOCUMENT GENERATION FORMAT (SHIP 30 ATOMIC ESSAY):\n"
                "The user requested an essay. Generate a high-impact, standalone Atomic Essay formatted in clean Markdown:\n"
                "1. Start directly with '# <Compelling Title>' on line 1. Do not prefix with conversational pleasantries (e.g. 'Sure, here is your essay:').\n"
                "2. Include a punchy hook or core thesis.\n"
                "3. Organize the body into clear sections with '## <Subheading>'.\n"
                "4. Use concise paragraphs, bullet points, and actionable takeaways.\n"
                "5. Ground the insights in Lenny's guest advice and frameworks where relevant.\n"
                "6. Conclude with a memorable summary or forward-looking takeaway.\n"
                "7. Do not include ASCII decorative lines (such as '====' or '----') under headings; use standard Markdown syntax."
            )
        elif art_type == "html":
            artifact_instruction = (
                "\n\nDOCUMENT GENERATION FORMAT (INTERACTIVE HTML TOOL):\n"
                "The user requested an interactive HTML artifact or dashboard. Provide clean, self-contained HTML/CSS/JS:\n"
                "1. Output valid, standalone HTML/CSS/JS. Do not add introductory conversational text.\n"
                "2. Include all necessary styles in an inline <style> block and logic in a <script> block.\n"
                "3. Ensure interactive controls (sliders, buttons) update displayed calculations dynamically.\n"
                "4. Keep the design clean, responsive, and compact so generation completes quickly."
            )
        else:
            artifact_instruction = (
                "\n\nDOCUMENT GENERATION FORMAT (STRATEGY GUIDE / PLAYBOOK / ARTIFACT):\n"
                "The user requested an artifact / strategy document. Generate a comprehensive, well-structured guide in clean Markdown:\n"
                "1. Start directly with '# <Document Title>' on line 1 without conversational filler.\n"
                "2. Structure with '## <Section Headings>' and '### <Subsections>'.\n"
                "3. Use clear paragraphs, structured tables, or bullet lists.\n"
                "4. Cite podcast guests, episodes, or frameworks where relevant.\n"
                "5. Do not include ASCII decorative lines (such as '===='); use standard Markdown '---' for horizontal dividers."
            )

    if not database_has_transcripts:
        return (
            f"{DEFAULT_BASE_PROMPT}\n\n"
            "SYSTEM NOTICE:\n"
            "No podcast transcripts have been indexed in the database yet. "
            "Transcripts can be ingested using the CLI: `python -m app.ingestion.cli --source data/samples`.\n"
            "Provide helpful answers using established product management and growth principles, "
            "but clearly inform the user that direct transcript grounding is currently unavailable "
            "until transcripts are ingested. Do not invent or fabricate quotes or timestamps."
            f"{artifact_instruction}"
        )

    if not retrieved_chunks:
        return (
            f"{DEFAULT_BASE_PROMPT}\n\n"
            "TRANSCRIPT SEARCH STATUS:\n"
            "The transcript database was searched, but no podcast excerpts met the relevance similarity threshold "
            "for this query.\n"
            "INSTRUCTIONS:\n"
            "1. Answer the query using general product management frameworks, but explicitly state that "
            "no directly relevant quotes or excerpts were found in Lenny's indexed transcripts.\n"
            "2. Do not invent quotes, timestamps, or episodes."
            f"{artifact_instruction}"
        )

    # We have genuine transcript excerpts!
    excerpts_text = []
    for i, chunk in enumerate(retrieved_chunks, start=1):
        ts = f" (Timestamp: {chunk.timestamp_start})" if chunk.timestamp_start else ""
        excerpts_text.append(
            f"[EXCERPT {i}]\n"
            f"Episode: {chunk.title}\n"
            f"Guest: {chunk.guest_name}{ts}\n"
            f"Content:\n{chunk.content}\n"
        )

    joined_excerpts = "\n---\n".join(excerpts_text)

    return (
        f"{DEFAULT_BASE_PROMPT}\n\n"
        "You have access to the following VERIFIED EXCERPTS from Lenny's Podcast transcripts:\n\n"
        f"{joined_excerpts}\n\n"
        "STRICT GROUNDING INSTRUCTIONS:\n"
        "1. Ground your answer in the provided transcript excerpts whenever discussing Lenny's Podcast episodes, "
        "guests, frameworks, or advice.\n"
        "2. Directly attribute quotes or insights to the respective guests (e.g., 'Brian Chesky explained...').\n"
        "3. Clearly distinguish between source-supported facts directly stated in the excerpts and your reasonable "
        "inferences or general product management advice.\n"
        "4. If the provided excerpts do not contain enough evidence to answer a specific detail, explicitly state "
        "that the available excerpts do not address that detail. Do NOT fabricate information, quotes, or timestamps."
        f"{artifact_instruction}"
    )


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit Chat Message",
    description="Accepts, validates, retrieves relevant transcript context, persists turns, and invokes the selected AI provider.",
)
async def submit_chat_message(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
) -> ChatResponse:
    """
    Processes chat query with pgvector RAG retrieval and selected LLM provider, saving turns to database.
    """
    session_id = request.session_id or f"session-{uuid.uuid4()}"
    selected_provider_name = (request.provider or settings.DEFAULT_MODEL_PROVIDER).strip().lower()

    # Detect artifact intent
    artifact_intent = detect_artifact_intent(request.message)

    logger.info(
        f"Processing chat message for session={session_id} "
        f"(provider={selected_provider_name}, length={len(request.message)} chars, artifact_intent={artifact_intent})"
    )

    # 1. Load prior conversation history for context before saving new message
    prior_messages = await SessionService.get_session_messages(db, session_id, limit=10)

    # 2. Persist User Message to Database
    try:
        await SessionService.save_message(
            db=db,
            session_id=session_id,
            role="user",
            content=request.message,
            provider=selected_provider_name,
        )
    except Exception as e:
        logger.warning(f"Could not persist user message to database: {type(e).__name__}")

    # 3. Step 07: Vector Retrieval from pgvector
    retrieved_chunks: List[RetrievedChunk] = []
    citations: List[Dict[str, Any]] = []
    database_has_transcripts = False

    try:
        indexed_count = await RetrievalService.get_indexed_chunk_count(db)
        database_has_transcripts = indexed_count > 0

        if database_has_transcripts:
            # Embed the user query
            embedder = get_embedding_provider()
            query_vector = await embedder.embed_text(request.message)

            # Retrieve top-k similar chunks
            retrieved_chunks = await RetrievalService.search_similar_chunks(
                db=db,
                query_embedding=query_vector,
                top_k=settings.RAG_TOP_K_CHUNKS,
                similarity_threshold=settings.RAG_SIMILARITY_THRESHOLD,
            )

            citations = [chunk.to_citation_dict() for chunk in retrieved_chunks]
        else:
            logger.info("Chat invoked with 0 indexed transcript chunks in database. Running in ungrounded mode.")

    except EmbeddingProviderError as e:
        logger.warning(f"Embedding provider unavailable during retrieval: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during RAG retrieval: {type(e).__name__}: {e}", exc_info=True)

    # 4. Construct System Prompt with Grounded Excerpts and Artifact Intent
    system_prompt = build_rag_system_prompt(
        retrieved_chunks=retrieved_chunks,
        database_has_transcripts=database_has_transcripts,
        artifact_intent=artifact_intent,
    )

    # 5. Assemble history payload for LLM
    conversation_payload = []
    for past in prior_messages:
        if past.role in ("user", "assistant"):
            conversation_payload.append({"role": past.role, "content": past.content})
    conversation_payload.append({"role": "user", "content": request.message})

    # 6. Invoke the provider abstraction
    response_status = "success"
    assistant_reply = ""

    try:
        provider = get_llm_provider(selected_provider_name)
        llm_result = await provider.generate_response(
            messages=conversation_payload,
            system_prompt=system_prompt,
        )
        assistant_reply = llm_result.text
        response_status = "success"
    except LLMConfigurationError as e:
        logger.info(f"Provider not configured: {e.message}")
        response_status = "not_configured"
        assistant_reply = (
            f"The Lenny Growth Assistant FastAPI backend received your message. "
            f"Model provider '{selected_provider_name}' is not configured: {e.message}"
        )
    except LLMConnectionError as e:
        logger.warning(f"Provider connection error: {e.message}")
        response_status = "unavailable"
        assistant_reply = (
            f"Could not reach model provider '{selected_provider_name}'. {e.message}"
        )
    except LLMAuthenticationError as e:
        logger.warning(f"Provider authentication error: {e.message}")
        response_status = "authentication_failed"
        assistant_reply = (
            f"Authentication failed for provider '{selected_provider_name}'. {e.message}"
        )
    except LLMModelNotFoundError as e:
        logger.warning(f"Model not found: {e.message}")
        response_status = "model_not_found"
        assistant_reply = (
            f"Model not found for provider '{selected_provider_name}'. {e.message}"
        )
    except LLMTimeoutError as e:
        logger.warning(f"Provider timeout: {e.message}")
        response_status = "timeout"
        assistant_reply = (
            f"Request to provider '{selected_provider_name}' timed out. {e.message}"
        )
    except LLMProviderError as e:
        logger.warning(f"Provider general error: {e.message}")
        response_status = "error"
        assistant_reply = (
            f"Provider '{selected_provider_name}' returned an error: {e.message}"
        )
    except Exception as e:
        logger.error(f"Unhandled error during chat generation: {type(e).__name__}", exc_info=True)
        response_status = "error"
        assistant_reply = (
            f"An unexpected error occurred while communicating with provider '{selected_provider_name}'."
        )

    # 7. Persist Assistant Reply and Citations to Database
    assistant_msg = None
    try:
        assistant_msg = await SessionService.save_message(
            db=db,
            session_id=session_id,
            role="assistant",
            content=assistant_reply,
            provider=selected_provider_name,
            sources_metadata=citations,
        )

        if citations and assistant_msg:
            await SessionService.save_citations(
                db=db,
                message_id=assistant_msg.id,
                citations=citations,
            )
    except Exception as e:
        logger.warning(f"Could not persist assistant message or citations: {type(e).__name__}")

    # 8. If artifact requested and response generated successfully, persist Artifact record
    created_artifact_meta = None
    created_artifact_id = None

    if response_status == "success" and artifact_intent and assistant_msg:
        try:
            title = extract_artifact_title(assistant_reply, request.message)
            artifact_record = await SessionService.save_artifact(
                db=db,
                session_id=session_id,
                message_id=assistant_msg.id,
                artifact_type=artifact_intent["type"],
                title=title,
                content=assistant_reply,
                version=1,
                is_demonstration=False,
            )
            if artifact_record:
                created_artifact_id = artifact_record.id
                created_artifact_meta = ArtifactMetadata(
                    id=artifact_record.id,
                    title=artifact_record.title,
                    type=artifact_record.artifact_type,
                    content=artifact_record.content,
                    session_id=artifact_record.session_id,
                    message_id=artifact_record.message_id,
                    version=artifact_record.version,
                    is_demonstration=artifact_record.is_demonstration,
                    created_at=artifact_record.created_at.isoformat() if artifact_record.created_at else None,
                )
                logger.info(
                    f"Created artifact record {created_artifact_id} ('{title}', type={artifact_intent['type']}) "
                    f"for session={session_id}"
                )
        except Exception as e:
            logger.error(f"Failed to create artifact record: {type(e).__name__}: {e}", exc_info=True)

    return ChatResponse(
        status=response_status,
        session_id=session_id,
        message=assistant_reply,
        sources=citations,
        provider=selected_provider_name,
        timestamp=datetime.now(timezone.utc).isoformat(),
        artifact=created_artifact_meta,
        artifact_id=created_artifact_id,
    )
