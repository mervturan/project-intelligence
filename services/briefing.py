"""Generate a concise outcome-oriented project brief."""
from __future__ import annotations

from services.database import get_project, project_snapshot


def generate_work_brief(project_id: int) -> str:
    project = get_project(project_id)
    snapshot = project_snapshot(project_id)

    latest_summary = snapshot["summaries"][-1] if snapshot["summaries"] else "No updates have been added yet."
    decisions = snapshot["decisions"][-3:]
    actions = snapshot["actions"][-5:]
    questions = snapshot["open_questions"][-3:]

    next_step = actions[0]["task"] if actions else "Add the next project update and define one concrete action."

    lines = [
        f"## {project['name']} — Work Brief",
        f"**Objective:** {project['objective'] or 'Not yet defined.'}",
        f"**Latest context:** {latest_summary}",
        "",
        "### Key decisions",
        *(f"- {item}" for item in decisions),
        "- None recorded yet." if not decisions else "",
        "",
        "### Open actions",
        *(
            f"- {item['task']}" + (f" — due {item['deadline']}" if item.get("deadline") else "")
            for item in actions
        ),
        "- None recorded yet." if not actions else "",
        "",
        "### Unresolved questions",
        *(f"- {item}" for item in questions),
        "- None recorded yet." if not questions else "",
        "",
        "### Recommended next step",
        f"**{next_step}**",
    ]
    return "\n".join(line for line in lines if line != "")
