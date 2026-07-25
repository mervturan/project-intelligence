"""Lightweight local retrieval and question answering."""
from __future__ import annotations

import re
from collections import Counter
from typing import Any

from services.database import get_notes, project_snapshot

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "for", "from", "how", "i",
    "in", "is", "it", "of", "on", "our", "the", "to", "was", "we", "what",
    "when", "which", "who", "why", "with",
}


def _tokens(text: str) -> Counter[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return Counter(word for word in words if word not in STOPWORDS and len(word) > 1)


def _score(query: str, content: str) -> float:
    q = _tokens(query)
    c = _tokens(content)
    if not q:
        return 0.0
    overlap = sum(min(q[token], c[token]) for token in q)
    return overlap / sum(q.values())


def answer_project_question(project_id: int, question: str) -> dict[str, Any]:
    notes = get_notes(project_id)
    ranked = sorted(notes, key=lambda n: _score(question, n["content"]), reverse=True)
    relevant = [n for n in ranked[:3] if _score(question, n["content"]) > 0]
    snapshot = project_snapshot(project_id)
    q = question.lower()

    if "decision" in q or "decid" in q or "choose" in q or "chosen" in q:
        body = snapshot["decisions"][-5:]
        answer = "### Relevant decisions\n" + ("\n".join(f"- {x}" for x in body) if body else "No decisions have been captured yet.")
    elif "task" in q or "action" in q or "next" in q or "overdue" in q:
        body = snapshot["actions"][-5:]
        answer = "### Relevant actions\n" + (
            "\n".join(f"- {x['task']}" + (f" — due {x['deadline']}" if x.get('deadline') else "") for x in body)
            if body else "No actions have been captured yet."
        )
    elif relevant:
        excerpts = [n["content"][:400] for n in relevant]
        answer = "### Evidence-based answer\n" + "\n\n".join(excerpts)
    else:
        answer = "I could not find enough matching project context yet. Add more notes or ask using terms that appear in the workspace."

    return {
        "answer": answer,
        "sources": [
            {"source": n["source"], "excerpt": n["content"][:500]} for n in relevant
        ],
    }
