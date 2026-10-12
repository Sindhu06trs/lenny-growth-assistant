import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import yaml

from app.core.logging_config import logger


@dataclass
class ParsedTranscript:
    """Structured representation of a parsed transcript file."""
    title: str
    guest_name: str
    repo_path: str
    file_sha256: str
    content: str
    youtube_url: Optional[str] = None
    video_id: Optional[str] = None
    publish_date: Optional[date] = None
    description: Optional[str] = None
    duration_seconds: Optional[int] = None
    extra_metadata: Dict[str, Any] = field(default_factory=dict)
    utterances: List[Dict[str, Any]] = field(default_factory=list)


TIMESTAMP_PATTERN = re.compile(r"\((\d{1,2}:\d{2}(?::\d{2})?)\)")
SPEAKER_TIMESTAMP_PATTERN = re.compile(
    r"^([A-Z][A-Za-z0-9\s\.\-'\&]+?)\s*\(((\d{1,2}:)?\d{2}:\d{2})\)\s*:\s*(.*)$",
    re.MULTILINE
)


def parse_timestamp_seconds(timestamp_str: Optional[str]) -> Optional[int]:
    """Converts '01:13:28' or '05:04' into total seconds."""
    if not timestamp_str:
        return None
    parts = timestamp_str.strip("() ").split(":")
    try:
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 1:
            return int(parts[0])
    except ValueError:
        return None
    return None


def format_youtube_timestamp_url(youtube_url: Optional[str], timestamp_str: Optional[str]) -> Optional[str]:
    """Appends '&t=87s' to YouTube video URLs."""
    if not youtube_url:
        return None
    secs = parse_timestamp_seconds(timestamp_str)
    if secs is None or secs <= 0:
        return youtube_url
    separator = "&" if "?" in youtube_url else "?"
    clean_url = re.sub(r"([?&])t=\d+s?", "", youtube_url)
    return f"{clean_url}{separator}t={secs}s"


def make_json_serializable(data: Any) -> Any:
    """Recursively converts dates, datetimes, and sets to JSON-serializable primitives."""
    if isinstance(data, (date, datetime)):
        return data.isoformat()
    elif isinstance(data, dict):
        return {str(k): make_json_serializable(v) for k, v in data.items()}
    elif isinstance(data, (list, tuple, set)):
        return [make_json_serializable(v) for v in data]
    return data


class TranscriptParser:
    """
    Parses Markdown (.md), plain text (.txt), and JSON (.json) transcript files.
    """

    @staticmethod
    def calculate_sha256(content: str) -> str:
        """Returns the SHA256 hex digest of file text."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @staticmethod
    def parse_file(file_path: Path, base_dir: Optional[Path] = None) -> Optional[ParsedTranscript]:
        """
        Parses a single transcript file, handling errors and malformed formats gracefully.
        """
        if not file_path.is_file():
            logger.warning(f"File does not exist: {file_path}")
            return None

        # Exclude known non-transcript files
        filename_lower = file_path.name.lower()
        if filename_lower in ("readme.md", "license", "license.md", ".gitkeep") or "index" in str(file_path.parent):
            return None

        try:
            raw_content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning(f"Could not read transcript file '{file_path}': {e}")
            return None

        if not raw_content.strip():
            logger.warning(f"Skipping empty transcript file: {file_path}")
            return None

        file_sha256 = TranscriptParser.calculate_sha256(raw_content)
        rel_path = str(file_path.relative_to(base_dir)) if base_dir else file_path.name

        ext = file_path.suffix.lower()
        if ext == ".md":
            return TranscriptParser._parse_markdown(raw_content, rel_path, file_sha256, file_path)
        elif ext == ".json":
            return TranscriptParser._parse_json(raw_content, rel_path, file_sha256, file_path)
        elif ext == ".txt":
            return TranscriptParser._parse_txt(raw_content, rel_path, file_sha256, file_path)
        else:
            logger.debug(f"Ignoring unsupported transcript extension: {ext} for {file_path}")
            return None

    @staticmethod
    def _parse_markdown(
        raw_content: str, rel_path: str, file_sha256: str, file_path: Path
    ) -> Optional[ParsedTranscript]:
        frontmatter: Dict[str, Any] = {}
        body = raw_content

        # Extract YAML frontmatter if delimited by '---'
        if raw_content.startswith("---"):
            parts = raw_content.split("---", 2)
            if len(parts) >= 3:
                yaml_block = parts[1]
                body = parts[2].strip()
                try:
                    loaded = yaml.safe_load(yaml_block)
                    if isinstance(loaded, dict):
                        frontmatter = loaded
                except Exception as e:
                    logger.warning(f"Malformed YAML frontmatter in '{rel_path}': {e}")

        # Derive title and guest
        parent_folder_name = file_path.parent.name.replace("-", " ").title()
        guest = frontmatter.get("guest") or parent_folder_name or "Unknown Guest"
        title = frontmatter.get("title") or f"{guest} - Lenny's Podcast"

        # YouTube and video IDs
        youtube_url = frontmatter.get("youtube_url")
        video_id = frontmatter.get("video_id")
        if not video_id and youtube_url:
            match = re.search(r"v=([A-Za-z0-9_\-]+)", youtube_url)
            if match:
                video_id = match.group(1)

        # Publish date
        raw_date = frontmatter.get("publish_date")
        publish_date: Optional[date] = None
        if isinstance(raw_date, date):
            publish_date = raw_date
        elif isinstance(raw_date, str):
            try:
                publish_date = datetime.strptime(raw_date.strip(), "%Y-%m-%d").date()
            except ValueError:
                pass

        # Duration
        raw_duration = frontmatter.get("duration_seconds")
        duration_seconds: Optional[int] = None
        if raw_duration is not None:
            try:
                duration_seconds = int(float(raw_duration))
            except (ValueError, TypeError):
                pass

        description = frontmatter.get("description")

        # Clean body text: remove markdown header noise like '# Title \n ## Transcript'
        cleaned_body = re.sub(r"^#\s+[^\n]+\n+", "", body)
        cleaned_body = re.sub(r"^##\s+Transcript\s*\n+", "", cleaned_body, flags=re.IGNORECASE)

        if not cleaned_body.strip():
            logger.warning(f"Transcript body empty after stripping headers in '{rel_path}'")
            return None

        # Extract utterances/paragraphs
        utterances = TranscriptParser._extract_utterances(cleaned_body, default_guest=guest)

        return ParsedTranscript(
            title=str(title).strip(),
            guest_name=str(guest).strip(),
            repo_path=rel_path,
            file_sha256=file_sha256,
            content=cleaned_body.strip(),
            youtube_url=youtube_url,
            video_id=video_id,
            publish_date=publish_date,
            description=str(description).strip() if description else None,
            duration_seconds=duration_seconds,
            extra_metadata=make_json_serializable(frontmatter),
            utterances=utterances,
        )

    @staticmethod
    def _parse_json(
        raw_content: str, rel_path: str, file_sha256: str, file_path: Path
    ) -> Optional[ParsedTranscript]:
        try:
            data = json.loads(raw_content)
        except Exception as e:
            logger.warning(f"Invalid JSON transcript in '{rel_path}': {e}")
            return None

        if not isinstance(data, dict):
            return None

        title = data.get("title") or file_path.stem.replace("-", " ").title()
        guest = data.get("guest") or data.get("guest_name") or "Unknown Guest"
        content = data.get("content") or data.get("transcript") or ""

        # If transcript contains a list of utterances
        utterances = []
        if "utterances" in data and isinstance(data["utterances"], list):
            for u in data["utterances"]:
                if isinstance(u, dict):
                    utterances.append({
                        "speaker": u.get("speaker", guest),
                        "timestamp": u.get("timestamp"),
                        "text": u.get("text", ""),
                    })
            if not content:
                content = "\n\n".join(
                    f"{u.get('speaker')}: {u.get('text')}" for u in utterances
                )

        if not content.strip():
            return None

        return ParsedTranscript(
            title=str(title),
            guest_name=str(guest),
            repo_path=rel_path,
            file_sha256=file_sha256,
            content=content.strip(),
            youtube_url=data.get("youtube_url"),
            video_id=data.get("video_id"),
            description=data.get("description"),
            extra_metadata=make_json_serializable(data),
            utterances=utterances,
        )

    @staticmethod
    def _parse_txt(
        raw_content: str, rel_path: str, file_sha256: str, file_path: Path
    ) -> Optional[ParsedTranscript]:
        title = file_path.stem.replace("-", " ").title()
        guest = file_path.parent.name.replace("-", " ").title()
        utterances = TranscriptParser._extract_utterances(raw_content, default_guest=guest)

        return ParsedTranscript(
            title=title,
            guest_name=guest,
            repo_path=rel_path,
            file_sha256=file_sha256,
            content=raw_content.strip(),
            utterances=utterances,
        )

    @staticmethod
    def _extract_utterances(text: str, default_guest: str = "Guest") -> List[Dict[str, Any]]:
        """
        Parses text for speaker lines like:
        'Brian Chesky (00:00:00): ...' or '(00:01:27): ...'
        """
        utterances = []
        current_speaker = default_guest
        current_timestamp = None

        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        for p in paragraphs:
            # Check for "Speaker (timestamp): text"
            match = re.match(r"^([A-Za-z0-9\s\.\-'\&]+?)\s*\(((\d{1,2}:)?\d{2}:\d{2})\)\s*:\s*(.*)$", p, re.DOTALL)
            if match:
                current_speaker = match.group(1).strip()
                current_timestamp = match.group(2).strip()
                utterance_text = match.group(4).strip()
                utterances.append({
                    "speaker": current_speaker,
                    "timestamp": current_timestamp,
                    "text": utterance_text,
                })
                continue

            # Check for "(timestamp): text"
            time_match = re.match(r"^\(((\d{1,2}:)?\d{2}:\d{2})\)\s*:\s*(.*)$", p, re.DOTALL)
            if time_match:
                current_timestamp = time_match.group(1).strip()
                utterance_text = time_match.group(3).strip()
                utterances.append({
                    "speaker": current_speaker,
                    "timestamp": current_timestamp,
                    "text": utterance_text,
                })
                continue

            # Paragraph without explicit header
            utterances.append({
                "speaker": current_speaker,
                "timestamp": current_timestamp,
                "text": p,
            })

        return utterances
