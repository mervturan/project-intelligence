"""Structured extraction service.

The default implementation is deterministic and runnable without API keys.
Replace `extract_note_intelligence` with a Granite/watsonx-backed implementation
when credentials are available.
"""
from __future__ import annotations

import re
from typing import Any

DECISION_MARKERS = ("agreed", "decided", "selected", "chosen", "will use", "we'll use")
ACTION_MARKERS = ("need to", "must", "should", "todo", "action:", "follow up", "test ", "prepare ")
QUESTION_MARKERS = ("?", "unclear", "whether", "open question")


def _sentences(text: str) -> list[str]:
    chunks = re.split(r"(?<=[.!?])\s+|\n+", text.strip())
    return [chunk.strip(" -•\t") for chunk in chunks if chunk.strip()]


def _deadline(sentence: str) -> str | None:
    patterns = [
        r"\b(?:by|before|due)\s+([A-Za-z]+(?:\s+\d{1,2})?)\b",
        r"\b(today|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
        r"\b(\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, sentence, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def _action_task(sentence: str) -> str:
    task = re.sub(r"^(i|we|the team)\s+", "", sentence, flags=re.IGNORECASE)
    task = re.sub(r"\b(?:by|before|due)\s+[A-Za-z]+(?:\s+\d{1,2})?\b", "", task, flags=re.IGNORECASE)
    return task.strip(" .")


def extract_note_intelligence(text: str) -> dict[str, Any]:
    sentences = _sentences(text)
    decisions: list[str] = []
    actions: list[dict[str, str | None]] = []
    open_questions: list[str] = []

    for sentence in sentences:
        lowered = sentence.lower()
        if any(marker in lowered for marker in DECISION_MARKERS):
            decisions.append(sentence.rstrip("."))
        if any(marker in lowered for marker in ACTION_MARKERS):
            actions.append(
                {
                    "task": _action_task(sentence),
                    "owner": "User" if lowered.startswith("i ") else None,
                    "deadline": _deadline(sentence),
                }
            )
        if any(marker in lowered for marker in QUESTION_MARKERS):
            open_questions.append(sentence.rstrip("."))

    summary = " ".join(sentences[:2]) if sentences else ""
    return {
        "summary": summary,
        "decisions": decisions,
        "actions": actions,
        "open_questions": open_questions,
        "entities": [],
        "model": "local-rule-based-starter",
    }
