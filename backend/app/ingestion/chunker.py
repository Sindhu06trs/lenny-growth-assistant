from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from app.ingestion.parser import ParsedTranscript


@dataclass
class TranscriptChunkData:
    """Represents a chunk prepared for insertion into transcript_chunks table."""
    chunk_id: str
    chunk_index: int
    content: str
    timestamp_start: Optional[str] = None
    timestamp_end: Optional[str] = None
    extra_metadata: Dict[str, Any] = field(default_factory=dict)


class TranscriptChunker:
    """
    Chunks transcript text into appropriately sized, overlapping segments
    while preserving timestamp ranges, speaker cues, and document metadata.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        min_chunk_length: int = 100,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_length = min_chunk_length

    def chunk_transcript(
        self,
        transcript_id: str,
        parsed: ParsedTranscript,
    ) -> List[TranscriptChunkData]:
        """
        Segments a parsed transcript using utterance boundaries and sliding windows.
        """
        chunks: List[TranscriptChunkData] = []
        utterances = parsed.utterances

        if utterances:
            chunks = self._chunk_by_utterances(transcript_id, parsed, utterances)
        else:
            chunks = self._chunk_by_text(transcript_id, parsed.content)

        return chunks

    def _chunk_by_utterances(
        self,
        transcript_id: str,
        parsed: ParsedTranscript,
        utterances: List[Dict[str, Any]],
    ) -> List[TranscriptChunkData]:
        chunks: List[TranscriptChunkData] = []
        current_chunk_utterances: List[Dict[str, Any]] = []
        current_length = 0
        chunk_index = 0

        for u in utterances:
            speaker = u.get("speaker", parsed.guest_name)
            timestamp = u.get("timestamp")
            text = u.get("text", "").strip()
            if not text:
                continue

            formatted_line = f"{speaker} ({timestamp}): {text}" if timestamp else f"{speaker}: {text}"
            line_len = len(formatted_line)

            if current_length + line_len > self.chunk_size and current_chunk_utterances:
                # Emit current chunk
                chunk = self._build_utterance_chunk(
                    transcript_id, chunk_index, current_chunk_utterances, parsed
                )
                if chunk and len(chunk.content.strip()) >= self.min_chunk_length:
                    chunks.append(chunk)
                    chunk_index += 1

                # Carry over last utterance for overlap if beneficial
                if len(current_chunk_utterances) > 1 and current_length > self.chunk_overlap:
                    current_chunk_utterances = [current_chunk_utterances[-1]]
                    current_length = len(current_chunk_utterances[0].get("text", ""))
                else:
                    current_chunk_utterances = []
                    current_length = 0

            current_chunk_utterances.append(u)
            current_length += line_len

        # Emit trailing chunk
        if current_chunk_utterances:
            chunk = self._build_utterance_chunk(
                transcript_id, chunk_index, current_chunk_utterances, parsed
            )
            if chunk and len(chunk.content.strip()) >= self.min_chunk_length:
                chunks.append(chunk)

        # Fallback if utterance chunking produced nothing (e.g. all snippets were very short)
        if not chunks and parsed.content.strip():
            chunks = self._chunk_by_text(transcript_id, parsed.content)

        return chunks

    def _build_utterance_chunk(
        self,
        transcript_id: str,
        chunk_index: int,
        utterance_list: List[Dict[str, Any]],
        parsed: ParsedTranscript,
    ) -> Optional[TranscriptChunkData]:
        if not utterance_list:
            return None

        text_lines = []
        speakers = set()
        timestamp_start = None
        timestamp_end = None

        for u in utterance_list:
            spk = u.get("speaker", parsed.guest_name)
            ts = u.get("timestamp")
            txt = u.get("text", "").strip()
            if spk:
                speakers.add(spk)
            if ts:
                if not timestamp_start:
                    timestamp_start = ts
                timestamp_end = ts

            line = f"{spk} ({ts}): {txt}" if ts else f"{spk}: {txt}"
            text_lines.append(line)

        content = "\n\n".join(text_lines)

        return TranscriptChunkData(
            chunk_id=f"{transcript_id}-c{chunk_index:04d}",
            chunk_index=chunk_index,
            content=content,
            timestamp_start=timestamp_start,
            timestamp_end=timestamp_end,
            extra_metadata={
                "speakers": list(speakers),
                "guest": parsed.guest_name,
                "title": parsed.title,
                "video_id": parsed.video_id,
            },
        )

    def _chunk_by_text(
        self,
        transcript_id: str,
        text: str,
    ) -> List[TranscriptChunkData]:
        """Simple text sliding window chunker."""
        chunks: List[TranscriptChunkData] = []
        text = text.strip()
        if not text:
            return chunks

        start = 0
        chunk_index = 0
        text_len = len(text)

        while start < text_len:
            end = min(start + self.chunk_size, text_len)
            # Find nearest paragraph or newline break
            if end < text_len:
                break_point = text.rfind("\n\n", start, end)
                if break_point != -1 and break_point > start + self.chunk_size // 2:
                    end = break_point
                else:
                    period_point = text.rfind(". ", start, end)
                    if period_point != -1 and period_point > start + self.chunk_size // 2:
                        end = period_point + 1

            chunk_content = text[start:end].strip()
            if len(chunk_content) >= self.min_chunk_length:
                chunks.append(
                    TranscriptChunkData(
                        chunk_id=f"{transcript_id}-c{chunk_index:04d}",
                        chunk_index=chunk_index,
                        content=chunk_content,
                    )
                )
                chunk_index += 1

            if end >= text_len:
                break
            start = max(end - self.chunk_overlap, start + 1)

        return chunks
