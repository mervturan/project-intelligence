"""ContextFlow MVP: turn scattered notes into decisions, actions, and next steps."""
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

st.set_page_config(page_title="ContextFlow", page_icon="🧠", layout="wide")
init_db()

st.title("🧠 ContextFlow")
st.caption("AI project memory that turns notes into decisions, actions, and next steps.")

with st.sidebar:
    st.header("Workspace")
    projects = list_projects()
    project_names = [p["name"] for p in projects]
    selected_name = st.selectbox("Project", project_names, index=0 if projects else None)

    with st.expander("Create a new project"):
        new_name = st.text_input("Project name", placeholder="e.g., MSc Dissertation")
        new_objective = st.text_area("Objective", placeholder="What outcome is this project trying to achieve?")
        if st.button("Create project", use_container_width=True):
            if not new_name.strip():
                st.error("Enter a project name.")
            else:
                create_project(new_name.strip(), new_objective.strip())
                st.success("Project created. Refresh the project selector.")

if not projects:
    st.info("Create your first project from the sidebar to begin.")
    st.stop()

project = next((p for p in projects if p["name"] == selected_name), projects[0])
project = get_project(project["id"])

st.subheader(project["name"])
if project["objective"]:
    st.write(project["objective"])

add_tab, memory_tab, ask_tab, brief_tab = st.tabs(
    ["Add notes", "Project memory", "Ask ContextFlow", "Work brief"]
)

with add_tab:
    st.markdown("### Add a meeting note or project update")
    source = st.text_input("Source", value="Meeting notes")
    note_text = st.text_area(
        "Note",
        height=250,
        placeholder=(
            "Paste a meeting transcript, research note, project update, or decision log.\n\n"
            "Example: We agreed to use SQuAD as the main dataset. I need to test "
            "Qwen 1.5B before Friday. FEVER will remain an optional extension."
        ),
    )
    if st.button("Analyse and save", type="primary"):
        if not note_text.strip():
            st.error("Add some note text first.")
        else:
            intelligence = extract_note_intelligence(note_text)
            add_note(project["id"], source.strip() or "Note", note_text.strip(), intelligence)
            st.success("Note saved and converted into structured project memory.")
            st.json(intelligence)

with memory_tab:
    snapshot = project_snapshot(project["id"])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Notes", len(snapshot["notes"]))
    c2.metric("Decisions", len(snapshot["decisions"]))
    c3.metric("Open actions", len(snapshot["actions"]))
    c4.metric("Open questions", len(snapshot["open_questions"]))

    st.markdown("### Decisions")
    if snapshot["decisions"]:
        for item in snapshot["decisions"]:
            st.write(f"- {item}")
    else:
        st.caption("No decisions extracted yet.")

    st.markdown("### Actions")
    if snapshot["actions"]:
        for action in snapshot["actions"]:
            deadline = f" — due {action['deadline']}" if action.get("deadline") else ""
            owner = f" ({action['owner']})" if action.get("owner") else ""
            st.write(f"- {action['task']}{owner}{deadline}")
    else:
        st.caption("No actions extracted yet.")

    st.markdown("### Open questions")
    if snapshot["open_questions"]:
        for item in snapshot["open_questions"]:
            st.write(f"- {item}")
    else:
        st.caption("No open questions extracted yet.")

    with st.expander("Raw notes"):
        for note in snapshot["notes"]:
            st.markdown(f"**{note['source']} · {note['created_at']}**")
            st.write(note["content"])
            st.divider()

with ask_tab:
    st.markdown("### Ask about the project")
    question = st.text_input(
        "Question",
        placeholder="What changed in our dataset strategy?",
    )
    if st.button("Answer question"):
        if not question.strip():
            st.error("Enter a question.")
        else:
            response = answer_project_question(project["id"], question.strip())
            st.markdown(response["answer"])
            if response["sources"]:
                with st.expander("Evidence used"):
                    for source_item in response["sources"]:
                        st.markdown(f"**{source_item['source']}**")
                        st.write(source_item["excerpt"])

with brief_tab:
    st.markdown("### Current project brief")
    if st.button("Generate work brief", type="primary"):
        brief = generate_work_brief(project["id"])
        st.markdown(brief)
