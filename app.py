"""Project Intelligence: turn scattered notes into decisions, actions, and next steps."""
from __future__ import annotations

import streamlit as st

from services.briefing import generate_work_brief
from services.database import (
    add_note,
    create_project,
    get_project,
    init_db,
    list_projects,
    project_snapshot,
)
from services.extraction import extract_note_intelligence
from services.retrieval import answer_project_question

st.set_page_config(
    page_title="Project Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)
init_db()

PROJECT_PAGES = {
    "Dashboard": "📊",
    "New note": "➕",
    "Knowledge base": "🗂️",
    "Ask AI": "💬",
    "Work brief": "📄",
}
MEMORY_VIEWS = ("Notes", "Decisions", "Actions", "Questions")


def go_to(page: str, *, memory_view: str | None = None) -> None:
    """Queue navigation and apply it safely at the beginning of the next rerun."""
    st.session_state.pending_page = page
    if memory_view is not None:
        st.session_state.pending_memory_view = memory_view
    st.rerun()


def choose_project(project_id: int) -> None:
    st.session_state.selected_project_id = project_id
    go_to("Dashboard")


# New browser sessions always start on Home.
st.session_state.setdefault("page", "Home")
st.session_state.setdefault("selected_project_id", None)
st.session_state.setdefault("memory_view", "Notes")

# Apply redirects before rendering any widgets.
if "pending_page" in st.session_state:
    st.session_state.page = st.session_state.pop("pending_page")
if "pending_memory_view" in st.session_state:
    st.session_state.memory_view = st.session_state.pop("pending_memory_view")

projects = list_projects()
project_ids = [project["id"] for project in projects]
if st.session_state.selected_project_id not in project_ids:
    st.session_state.selected_project_id = None
    if st.session_state.page != "Home":
        st.session_state.page = "Home"


# -----------------------------------------------------------------------------
# Persistent collapsible sidebar
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🧠 Project Intelligence")
    st.caption("Project memory and decision support")

    if st.button("🏠 Home", use_container_width=True, type="primary" if st.session_state.page == "Home" else "secondary"):
        go_to("Home")

    if projects:
        st.divider()
        project_lookup = {project["id"]: project["name"] for project in projects}
        selected_index = 0
        if st.session_state.selected_project_id in project_ids:
            selected_index = project_ids.index(st.session_state.selected_project_id)

        selected_id = st.selectbox(
            "Current project",
            project_ids,
            index=selected_index,
            format_func=lambda project_id: project_lookup[project_id],
            key="project_selector",
        )
        if selected_id != st.session_state.selected_project_id:
            st.session_state.selected_project_id = selected_id
            go_to("Dashboard")

    else:
        st.divider()
        st.info("Create a project from Home to begin.")

    st.divider()
    st.caption("Use the arrow at the top to collapse or reopen this navigation.")


# -----------------------------------------------------------------------------
# Home page
# -----------------------------------------------------------------------------
if st.session_state.page == "Home":
    st.title("🧠 Project Intelligence")
    st.subheader("Turn project notes into decisions, actions, and clear next steps.")
    st.write(
        "Create a workspace, add meeting notes or updates, and build a searchable "
        "memory of what your team decided and what needs to happen next."
    )

    left, right = st.columns([1.1, 1])
    with left:
        st.markdown("### Create a new project")
        with st.form("home_create_project_form", clear_on_submit=True):
            new_name = st.text_input("Project name", placeholder="e.g., Version 3.0 Release")
            new_objective = st.text_area(
                "Objective",
                placeholder="What outcome is this project trying to achieve?",
                height=120,
            )
            create_submitted = st.form_submit_button(
                "Create project",
                type="primary",
                use_container_width=True,
            )

        if create_submitted:
            if not new_name.strip():
                st.error("Enter a project name.")
            else:
                new_project_id = create_project(new_name.strip(), new_objective.strip())
                if new_project_id == 0:
                    st.error("A project with this name already exists.")
                else:
                    st.session_state.selected_project_id = new_project_id
                    st.session_state.project_created_name = new_name.strip()
                    go_to("Dashboard")

    with right:
        st.markdown("### Your projects")
        if projects:
            for project_item in projects:
                with st.container(border=True):
                    st.markdown(f"#### 📁 {project_item['name']}")
                    st.caption(project_item["objective"] or "No objective added yet.")
                    if st.button(
                        "Open project →",
                        key=f"open_project_{project_item['id']}",
                        use_container_width=True,
                    ):
                        choose_project(project_item["id"])
        else:
            st.info("No projects yet. Create the first one on the left.")
    st.stop()


# All project pages require an active project.
if st.session_state.selected_project_id is None:
    go_to("Home")

project = get_project(st.session_state.selected_project_id)
snapshot = project_snapshot(project["id"])


# -----------------------------------------------------------------------------
# Persistent project header and quick navigation
# -----------------------------------------------------------------------------
st.title(project["name"])
if project.get("objective"):
    st.caption(project["objective"])

nav_cols = st.columns(5)
for column, (page_name, icon) in zip(nav_cols, PROJECT_PAGES.items()):
    with column:
        if st.button(
            f"{icon} {page_name}",
            key=f"top_{page_name}",
            use_container_width=True,
            type="primary" if st.session_state.page == page_name else "secondary",
        ):
            go_to(page_name)

st.divider()


# -----------------------------------------------------------------------------
# Dashboard
# -----------------------------------------------------------------------------
if st.session_state.page == "Dashboard":
    created_name = st.session_state.pop("project_created_name", None)
    if created_name:
        st.success(f'Project "{created_name}" was created successfully.')

    st.subheader("Project dashboard")

    # Clickable metric cards.
    metric_cols = st.columns(4)
    cards = [
        ("📝 Notes", len(snapshot["notes"]), "Notes"),
        ("✅ Decisions", len(snapshot["decisions"]), "Decisions"),
        ("📋 Open actions", len(snapshot["actions"]), "Actions"),
        ("❓ Open questions", len(snapshot["open_questions"]), "Questions"),
    ]
    for col, (label, value, view) in zip(metric_cols, cards):
        with col:
            with st.container(border=True):
                st.markdown(f"#### {label}")
                st.markdown(f"# {value}")
                if st.button(
                    f"View {view.lower()} →",
                    key=f"metric_{view}",
                    use_container_width=True,
                ):
                    go_to("Knowledge base", memory_view=view)

    left, right = st.columns(2)
    with left:
        st.markdown("### Recent notes")
        if snapshot["notes"]:
            for note in reversed(snapshot["notes"][-3:]):
                with st.container(border=True):
                    st.markdown(f"**{note['source']}**")
                    st.caption(note["created_at"])
                    preview = note["content"].replace("\n", " ")
                    st.write(preview[:180] + ("…" if len(preview) > 180 else ""))
        else:
            st.info("No notes yet. Add the first project update.")

    with right:
        st.markdown("### Latest decisions")
        if snapshot["decisions"]:
            for decision in snapshot["decisions"][-5:]:
                st.write(f"- {decision}")
        else:
            st.info("No decisions have been extracted yet.")


# -----------------------------------------------------------------------------
# New note
# -----------------------------------------------------------------------------
elif st.session_state.page == "New note":
    st.subheader("Add a meeting note or project update")

    if st.session_state.pop("note_saved", False):
        intelligence = st.session_state.get("last_saved_intelligence", {})
        st.success("Meeting note processed and added to project memory.")
        r1, r2, r3 = st.columns(3)
        r1.metric("Decisions extracted", len(intelligence.get("decisions", [])))
        r2.metric("Actions extracted", len(intelligence.get("actions", [])))
        r3.metric("Questions extracted", len(intelligence.get("open_questions", [])))

        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button("📊 Back to project dashboard", use_container_width=True):
                go_to("Dashboard")
        with b2:
            if st.button("🗂️ View project memory", use_container_width=True):
                go_to("Knowledge base")
        with b3:
            if st.button("💬 Ask about the project", use_container_width=True):
                go_to("Ask AI")
        st.divider()

    with st.form("add_note_form", clear_on_submit=True):
        source = st.text_input(
            "Note title or source",
            value="Meeting notes",
            placeholder="e.g., Sprint Review Meeting",
        )
        note_text = st.text_area(
            "Note",
            height=280,
            placeholder=(
                "Paste a meeting transcript, project update, or decision log.\n\n"
                "Example: The team agreed to freeze new features by August 12. "
                "Emily will complete authentication by Tuesday."
            ),
        )
        note_submitted = st.form_submit_button(
            "Analyse and save",
            type="primary",
            use_container_width=True,
        )

    if note_submitted:
        if not note_text.strip():
            st.error("Add some note text first.")
        else:
            intelligence = extract_note_intelligence(note_text)
            add_note(project["id"], source.strip() or "Note", note_text.strip(), intelligence)
            st.session_state.last_saved_intelligence = intelligence
            st.session_state.note_saved = True
            go_to("New note")


# -----------------------------------------------------------------------------
# Knowledge base
# -----------------------------------------------------------------------------
elif st.session_state.page == "Knowledge base":
    st.subheader("Project knowledge base")

    view_cols = st.columns(4)
    for col, view in zip(view_cols, MEMORY_VIEWS):
        with col:
            if st.button(
                view,
                key=f"memory_{view}",
                use_container_width=True,
                type="primary" if st.session_state.memory_view == view else "secondary",
            ):
                st.session_state.memory_view = view
                st.rerun()

    st.divider()
    view = st.session_state.memory_view

    if view == "Notes":
        st.markdown("### Meeting notes and updates")
        if snapshot["notes"]:
            for note in reversed(snapshot["notes"]):
                with st.expander(f"{note['source']} · {note['created_at']}"):
                    st.write(note["content"])
                    st.markdown("**Extracted summary**")
                    st.write(note["intelligence"].get("summary") or "No summary extracted.")
        else:
            st.info("No notes have been added yet.")

    elif view == "Decisions":
        st.markdown("### Decisions")
        if snapshot["decisions"]:
            for index, item in enumerate(snapshot["decisions"], start=1):
                st.write(f"**{index}.** {item}")
        else:
            st.info("No decisions have been extracted yet.")

    elif view == "Actions":
        st.markdown("### Open actions")
        if snapshot["actions"]:
            for action in snapshot["actions"]:
                owner = f" — **Owner:** {action['owner']}" if action.get("owner") else ""
                deadline = f" — **Due:** {action['deadline']}" if action.get("deadline") else ""
                st.write(f"- {action['task']}{owner}{deadline}")
        else:
            st.info("No actions have been extracted yet.")

    elif view == "Questions":
        st.markdown("### Open questions")
        if snapshot["open_questions"]:
            for item in snapshot["open_questions"]:
                st.write(f"- {item}")
        else:
            st.info("No open questions have been extracted yet.")


# -----------------------------------------------------------------------------
# Ask AI
# -----------------------------------------------------------------------------
elif st.session_state.page == "Ask AI":
    st.subheader("Ask Project Intelligence")
    st.caption("Ask about decisions, tasks, deadlines, or previous project discussions.")

    with st.form("question_form"):
        question = st.text_input(
            "Question",
            placeholder="What decisions have been made?",
        )
        question_submitted = st.form_submit_button("Answer question", type="primary")

    if question_submitted:
        if not question.strip():
            st.error("Enter a question.")
        else:
            st.session_state.last_question_response = answer_project_question(
                project["id"], question.strip()
            )

    response = st.session_state.get("last_question_response")
    if response:
        st.markdown(response["answer"])
        if response["sources"]:
            with st.expander("Evidence used"):
                for source_item in response["sources"]:
                    st.markdown(f"**{source_item['source']}**")
                    st.write(source_item["excerpt"])


# -----------------------------------------------------------------------------
# Work brief
# -----------------------------------------------------------------------------
elif st.session_state.page == "Work brief":
    st.subheader("Current project brief")
    st.caption("Generate a concise view of the project's position, decisions, actions, and questions.")

    if st.button("Generate work brief", type="primary", use_container_width=True):
        st.session_state.current_brief_project_id = project["id"]
        st.session_state.current_brief = generate_work_brief(project["id"])

    if (
        "current_brief" in st.session_state
        and st.session_state.get("current_brief_project_id") == project["id"]
    ):
        with st.container(border=True):
            st.markdown(st.session_state.current_brief)
    else:
        st.info("Select Generate work brief to create the latest project summary.")
