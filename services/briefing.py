"""Generate a concise project brief from stored project intelligence."""
from __future__ import annotations

from services.database import get_project, project_snapshot


def generate_work_brief(project_id: int) -> str:
    project = get_project(project_id)
    snapshot = project_snapshot(project_id)

    lines = [f"## {project['name']} — Work Brief"]
    if project.get("objective"):
        lines.extend(["", f"**Objective:** {project['objective']}"])

    lines.extend(["", "### Current position"])
    if snapshot["summaries"]:
        lines.append(snapshot["summaries"][-1])
    elif snapshot["notes"]:
        lines.append("Project notes are available, but no summary has been extracted yet.")
    else:
        lines.append("No project notes have been added yet.")

    lines.extend(["", "### Decisions"])
    if snapshot["decisions"]:
        lines.extend(f"- {item}" for item in snapshot["decisions"])
    else:
        lines.append("- No decisions recorded yet.")

    lines.extend(["", "### Next actions"])
    if snapshot["actions"]:
        for action in snapshot["actions"]:
            owner = f" — Owner: {action['owner']}" if action.get("owner") else ""
            deadline = f" — Due: {action['deadline']}" if action.get("deadline") else ""
            lines.append(f"- {action['task']}{owner}{deadline}")
    else:
        lines.append("- No actions recorded yet.")

    lines.extend(["", "### Open questions"])
    if snapshot["open_questions"]:
        lines.extend(f"- {item}" for item in snapshot["open_questions"])
    else:
        lines.append("- No open questions recorded.")

    return "\n".join(lines)
