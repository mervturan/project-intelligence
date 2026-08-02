"""Project Intelligence: collaborative project memory and decision support."""
from __future__ import annotations

import html
from typing import Any
import streamlit as st

from services.briefing import generate_work_brief
from services.database import (
    add_note,
    update_note,
    delete_note,
    add_project_member,
    create_project,
    delete_project,
    discover_public_projects,
    get_or_create_user,
    get_project,
    get_user,
    init_db,
    list_collaboration_requests,
    list_project_members,
    list_projects,
    project_snapshot,
    remove_project_member,
    rename_project,
    request_collaboration,
    resolve_collaboration_request,
    search_users,
    set_project_visibility,
    toggle_project_star,
    update_project_objective,
    user_can_access_project,
    user_is_owner,
)
from services.extraction import extract_note_intelligence
from services.retrieval import answer_project_question

st.set_page_config(
    page_title="Project Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)
init_db()

PROJECT_PAGES = {
    "Dashboard": "📊",
    "New note": "➕",
    "Knowledge base": "🗂️",
    "Ask AI": "💬",
    "Work brief": "📄",
    "Team": "👥",
}
MEMORY_VIEWS = ("Notes", "Decisions", "Actions", "Questions")


def current_user_id() -> int | None:
    value = st.session_state.get("user_id")
    return int(value) if value is not None else None


def go_to(page: str, *, memory_view: str | None = None) -> None:
    st.session_state.pending_page = page
    if memory_view is not None:
        st.session_state.pending_memory_view = memory_view
    st.rerun()


def choose_project(project_id: int) -> None:
    if not user_can_access_project(project_id, current_user_id()):
        st.error("You do not have access to that project.")
        return
    st.session_state.selected_project_id = project_id
    go_to("Dashboard")


st.session_state.setdefault("page", "Home")
st.session_state.setdefault("selected_project_id", None)
st.session_state.setdefault("memory_view", "Notes")
st.session_state.setdefault("user_id", None)

if "pending_page" in st.session_state:
    st.session_state.page = st.session_state.pop("pending_page")
if "pending_memory_view" in st.session_state:
    st.session_state.memory_view = st.session_state.pop("pending_memory_view")

# Text-link navigation uses lightweight query parameters.
requested_page = st.query_params.get("page")
requested_project = st.query_params.get("project_id")
if requested_page in {"Home", "About", "Contact"}:
    st.session_state.page = requested_page
    if requested_page == "Home":
        st.session_state.selected_project_id = None
    st.query_params.clear()
elif requested_page == "Dashboard" and requested_project:
    try:
        project_id = int(requested_project)
    except (TypeError, ValueError):
        project_id = None
    if project_id and user_can_access_project(project_id, current_user_id()):
        st.session_state.selected_project_id = project_id
        st.session_state.page = "Dashboard"
    st.query_params.clear()

# Validate selected project against current access.
if st.session_state.selected_project_id is not None:
    if not user_can_access_project(int(st.session_state.selected_project_id), current_user_id()):
        st.session_state.selected_project_id = None
        st.session_state.page = "Home"

st.markdown(
    """
    <style>
      .block-container { padding-top: 5.5rem; padding-bottom: 3rem; max-width: 1240px; }
      [data-testid="stAppViewContainer"] > .main { overflow:visible; }
      .home-hero {
        min-height: 62vh; display:flex; flex-direction:column; align-items:center;
        justify-content:center; padding:5rem 1rem 6rem;
      }
      .home-title {
        text-align:center; font-size:clamp(3.3rem,8vw,7rem); font-weight:800;
        letter-spacing:-.055em; margin:0 0 .8rem;
        background:linear-gradient(90deg,#ffffff 0%,#ffffff 26%,#f5b6dc 42%,#d79cff 60%,#9d6cff 78%,#6f3fd6 100%);
        background-size:320% auto; background-position:0% center; color:transparent; -webkit-background-clip:text;
        background-clip:text; animation:titleReveal 2.4s ease-out forwards;
      }
      .home-subtitle { text-align:center; font-size:clamp(1rem,2vw,1.25rem); color:#777985; max-width:720px; }
      .scroll-cue { text-align:center; color:#9a9ca6; font-size:.92rem; margin-top:2.3rem; animation:cueFloat 1.8s ease-in-out infinite; }
      .project-meta { color:#858793; margin-top:.1rem; margin-bottom:1rem; }
      .access-pill { display:inline-block; padding:.2rem .55rem; border-radius:999px; background:#f2f3f7; font-size:.78rem; color:#555865; }
      @keyframes headerBrandReveal { 0%{background-position:0% center} 100%{background-position:100% center} }
      @keyframes cueFloat { 0%,100%{transform:translateY(0)} 50%{transform:translateY(6px)} }
      @keyframes titleReveal { 0%{opacity:.25;transform:translateY(12px);background-position:0% center} 35%{opacity:1} 100%{opacity:1;transform:translateY(0);background-position:100% center} }
      .st-key-app_header {
        position:relative; z-index:20; padding:1rem 1.15rem .9rem; margin-top:.35rem;
        border:1px solid rgba(222,210,198,.72); border-radius:1rem; margin-bottom:1.15rem; overflow:visible;
        background:linear-gradient(110deg,rgba(255,246,252,.96) 0%,rgba(241,229,255,.94) 45%,rgba(244,226,199,.92) 100%);
        box-shadow:0 8px 28px rgba(100,74,128,.08);
      }
      .st-key-app_header [data-testid="stHorizontalBlock"] { align-items:center; }
      .st-key-app_header [data-testid="column"] { overflow:visible; }
      .brand-link {
        display:inline-block; font-weight:800; font-size:1.12rem; text-decoration:none !important;
        background:linear-gradient(90deg,#ffffff 0%,#ffffff 25%,#ec7fbd 48%,#bb72ef 72%,#7d5ce2 100%);
        background-size:300% auto; background-position:0% center;
        -webkit-background-clip:text; background-clip:text; color:transparent !important;
        animation:headerBrandReveal 2.1s ease-out forwards; transition:transform .18s ease, filter .18s ease;
      }
      .brand-link:hover { transform:translateY(-1px); filter:drop-shadow(0 0 8px rgba(187,114,239,.28)); }
      .st-key-app_header button { border:0 !important; background:transparent !important; box-shadow:none !important; }
      /* Calm default buttons: white surface with subtle neutral border. */
      div.stButton > button, div[data-testid="stFormSubmitButton"] > button {
        background:#ffffff !important; color:#34343d !important; border:1px solid #dedee8 !important;
        box-shadow:0 2px 7px rgba(45,39,72,.04) !important; transition:transform .16s ease, border-color .16s ease, box-shadow .16s ease, background .16s ease !important;
      }
      div.stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {
        transform:translateY(-2px); border-color:#b58ae8 !important; box-shadow:0 7px 18px rgba(139,92,214,.13) !important;
      }
      /* Primary and home-return actions use the brand purple. */
      div.stButton > button[kind="primary"], div[data-testid="stFormSubmitButton"] > button[kind="primary"] {
        background:linear-gradient(100deg,#a85fd5,#7b5ce1) !important; color:white !important; border-color:transparent !important;
      }
      div.stButton > button[kind="primary"]:hover, div[data-testid="stFormSubmitButton"] > button[kind="primary"]:hover {
        background:#ffffff !important; color:#7b50d0 !important; border-color:#8d62df !important;
      }
      /* Destructive controls are the only red actions. */
      [class*="st-key-delete_"] button, [class*="st-key-confirm_delete"] button,
      [class*="st-key-project_header_delete"] button, [class*="st-key-delete_project"] button {
        background:#fff6f7 !important; color:#b4233c !important; border-color:#f0a8b5 !important;
      }
      [class*="st-key-delete_"] button:hover, [class*="st-key-confirm_delete"] button:hover,
      [class*="st-key-project_header_delete"] button:hover, [class*="st-key-delete_project"] button:hover {
        background:#b4233c !important; color:white !important; border-color:#b4233c !important;
      }
      /* Header/footer links read as text, not boxed buttons. */
      .st-key-app_header [data-testid="column"]:nth-child(2) button,
      .st-key-app_header [data-testid="column"]:nth-child(3) button,
      [class*="st-key-footer_"] button {
        border:0 !important; box-shadow:none !important; background:transparent !important; color:#696774 !important;
      }
      .st-key-app_header [data-testid="column"]:nth-child(2) button:hover,
      .st-key-app_header [data-testid="column"]:nth-child(3) button:hover,
      [class*="st-key-footer_"] button:hover {
        color:#8c58d5 !important; transform:translateY(-1px); text-decoration:underline;
      }
      .st-key-project_title_bar { margin-top:.35rem; padding:.55rem 0 .25rem; overflow:visible; }
      .st-key-project_title_bar button { border:0 !important; background:transparent !important; box-shadow:none !important; }
      /* Project title: target the first button in the title bar directly.
         This is stronger and more reliable than relying only on the widget-key class. */
      .st-key-project_title_bar [data-testid="column"]:first-child button,
      [class*="st-key-project_title_dashboard"] button {
        display:inline-flex !important;
        align-items:center !important;
        width:auto !important;
        min-height:0 !important;
        height:auto !important;
        padding:0 0 .35rem 0 !important;
        margin:0 !important;
        background:transparent !important;
        border:0 !important;
        box-shadow:none !important;
        color:#202127 !important;
        text-align:left !important;
        white-space:normal !important;
        font-family:inherit !important;
        font-size:clamp(2.9rem,5.5vw,4.1rem) !important;
        font-weight:800 !important;
        line-height:1.08 !important;
        letter-spacing:-.025em !important;
        word-spacing:normal !important;
        text-decoration:none !important;
        transition:color .18s ease, transform .18s ease !important;
      }
      .st-key-project_title_bar [data-testid="column"]:first-child button *,
      [class*="st-key-project_title_dashboard"] button * {
        font-family:inherit !important;
        font-size:inherit !important;
        font-weight:inherit !important;
        line-height:inherit !important;
        letter-spacing:inherit !important;
        word-spacing:inherit !important;
        color:inherit !important;
        margin:0 !important;
        padding:0 !important;
      }
      .st-key-project_title_bar [data-testid="column"]:first-child button:hover,
      [class*="st-key-project_title_dashboard"] button:hover {
        color:#8c58d5 !important;
        transform:translateY(-1px) !important;
        background:transparent !important;
      }
      .st-key-project_title_bar [data-testid="column"]:first-child button:focus,
      [class*="st-key-project_title_dashboard"] button:focus {
        box-shadow:none !important;
      }
      .st-key-project_title_bar [data-testid="column"]:not(:first-child) { opacity:.42; transition:opacity .18s ease, transform .18s ease; }
      .st-key-project_title_bar:hover [data-testid="column"]:not(:first-child),
      .st-key-project_title_bar:focus-within [data-testid="column"]:not(:first-child) { opacity:1; transform:translateY(-1px); }
      .st-key-project_title_bar [data-testid="column"]:not(:first-child) button { font-size:1.2rem; padding:.25rem; color:#6f6478 !important; }
      .st-key-project_title_bar [data-testid="column"]:not(:first-child) button:hover { color:#8c58d5 !important; }
      .project-objective { color:#777985; font-size:1rem; margin:-.25rem 0 1rem; }
      .site-footer {
        margin-top:4rem; padding:1.35rem 1rem; border:1px solid rgba(222,210,198,.72); border-radius:1rem;
        color:#77727d; text-align:center; font-size:.88rem;
        background:linear-gradient(110deg,rgba(255,246,252,.96) 0%,rgba(241,229,255,.94) 45%,rgba(244,226,199,.92) 100%);
      }
      .nav-text-links { display:flex; align-items:center; justify-content:flex-end; gap:1.3rem; height:100%; }
      .nav-text-link, .footer-text-link { color:#696774 !important; text-decoration:none !important; font-weight:600; transition:color .18s ease, transform .18s ease; }
      .nav-text-link:hover, .footer-text-link:hover { color:#8c58d5 !important; text-decoration:none !important; }
      .nav-text-link:hover { transform:translateY(-1px); }
      .footer-links { display:flex; justify-content:center; gap:1.2rem; margin-top:.65rem; flex-wrap:wrap; }

      [data-testid="stSidebar"] .sidebar-brand {
        font-size:1.35rem; font-weight:800; margin:.2rem 0 .8rem;
        background:linear-gradient(90deg,#ec7fbd,#bb72ef,#7d5ce2);
        -webkit-background-clip:text; background-clip:text; color:transparent;
      }
      [data-testid="collapsedControl"]:hover::after {
        content:"Open navigation for more options"; position:absolute; left:3rem; top:.4rem;
        white-space:nowrap; background:#24252d; color:white; padding:.38rem .58rem; border-radius:.45rem;
        font-size:.78rem; box-shadow:0 4px 16px rgba(0,0,0,.16);
      }
      @media (max-width: 760px), (hover:none) {
        .block-container { padding-left:1rem; padding-right:1rem; padding-top:5rem; }
        .home-hero { min-height:52vh; padding:3rem .5rem 4rem; }
        .st-key-project_title_bar [data-testid="column"]:not(:first-child) { opacity:1; }
        .st-key-project_title_bar [data-testid="stHorizontalBlock"] { gap:.15rem; }
        .st-key-project_title_bar [data-testid="column"]:first-child { min-width:100% !important; flex-basis:100% !important; }
        .st-key-project_title_bar [data-testid="column"]:not(:first-child) { min-width:46px !important; flex:0 0 46px !important; }
        .st-key-app_header [data-testid="stHorizontalBlock"] { flex-wrap:wrap; }
        .st-key-workspace_nav [data-testid="stHorizontalBlock"] { flex-wrap:wrap; gap:.35rem; }
        .st-key-workspace_nav [data-testid="column"] { min-width:145px !important; flex:1 1 145px !important; }
        [data-testid="stSidebar"] { min-width:260px; }
      }
    </style>
    """,
    unsafe_allow_html=True,
)

@st.dialog("Sign in to Project Intelligence")
def login_dialog() -> None:
    st.caption("This lightweight hackathon login demonstrates user-specific workspaces. It is not production authentication.")
    display_name = st.text_input("Display name", placeholder="Alex Morgan")
    username = st.text_input("Username", placeholder="alex_morgan")
    if st.button("Continue", type="primary", use_container_width=True):
        if not username.strip():
            st.error("Enter a username.")
        else:
            user = get_or_create_user(username.strip(), display_name.strip())
            st.session_state.user_id = int(user["id"])
            st.session_state.login_success = user["display_name"]
            st.rerun()


@st.dialog("Rename project")
def rename_dialog(project_id: int) -> None:
    project = get_project(project_id)
    new_name = st.text_input("Project name", value=project["name"], key=f"rename_{project_id}")
    left, right = st.columns(2)
    if left.button("Save", type="primary", use_container_width=True):
        cleaned = new_name.strip()
        if not cleaned:
            st.error("Enter a project name.")
        elif not rename_project(project_id, cleaned):
            st.error("You already have a project with that name.")
        else:
            st.session_state.rename_success = cleaned
            st.rerun()
    if right.button("Cancel", use_container_width=True):
        st.rerun()


@st.dialog("Edit project objective")
def objective_dialog(project_id: int) -> None:
    project = get_project(project_id)
    objective = st.text_area(
        "Project objective",
        value=project.get("objective") or "",
        height=160,
        placeholder="What outcome is the team working toward?",
        key=f"objective_{project_id}",
    )
    left, right = st.columns(2)
    if left.button("Save objective", type="primary", use_container_width=True):
        update_project_objective(project_id, objective.strip())
        st.session_state.objective_success = True
        st.rerun()
    if right.button("Cancel", use_container_width=True):
        st.rerun()


@st.dialog("Delete project?")
def delete_dialog(project_id: int) -> None:
    project = get_project(project_id)
    st.warning(f'Are you sure you want to delete “{project["name"]}”?')
    st.write("Its notes, decisions, actions, questions, and collaboration settings will be removed. This cannot be undone.")
    left, right = st.columns(2)
    if left.button("Delete permanently", type="primary", use_container_width=True):
        delete_project(project_id)
        st.session_state.selected_project_id = None
        st.session_state.page = "Home"
        st.session_state.delete_success = project["name"]
        st.rerun()
    if right.button("Cancel", use_container_width=True):
        st.rerun()


@st.dialog("Edit meeting note")
def edit_note_dialog(note: dict[str, Any]) -> None:
    source = st.text_input("Note title or source", value=note["source"], key=f"edit_source_{note['id']}")
    content = st.text_area("Note", value=note["content"], height=320, key=f"edit_content_{note['id']}")
    left, right = st.columns(2)
    if left.button("Save changes", type="primary", use_container_width=True, key=f"save_note_{note['id']}"):
        if not content.strip():
            st.error("The note cannot be empty.")
        else:
            intelligence = extract_note_intelligence(content.strip())
            update_note(int(note["id"]), source.strip() or "Note", content.strip(), intelligence)
            st.session_state.generated_brief = None
            st.session_state.note_updated_name = source.strip() or "Note"
            st.rerun()
    if right.button("Cancel", use_container_width=True, key=f"cancel_note_{note['id']}"):
        st.rerun()


@st.dialog("Delete meeting note?")
def delete_note_dialog(note: dict[str, Any]) -> None:
    st.warning(f'This will permanently delete “{note["source"]}” and remove its extracted information from project memory.')
    left, right = st.columns(2)
    if left.button("Delete permanently", type="primary", use_container_width=True, key=f"confirm_delete_note_{note['id']}"):
        deleted_name = note["source"]
        delete_note(int(note["id"]))
        st.session_state.generated_brief = None
        st.session_state.note_deleted_name = deleted_name
        st.rerun()
    if right.button("Cancel", use_container_width=True, key=f"cancel_delete_note_{note['id']}"):
        st.rerun()


def sign_out() -> None:
    st.session_state.user_id = None
    st.session_state.selected_project_id = None
    st.session_state.page = "Home"
    st.rerun()


def render_app_header() -> None:
    user = get_user(current_user_id()) if current_user_id() else None
    with st.container(key="app_header"):
        cols = st.columns([4.8, 2.4, 1.8])
        cols[0].markdown(
            '<a class="brand-link" href="?page=Home" target="_self">🧠 Project Intelligence</a>',
            unsafe_allow_html=True,
        )
        cols[1].markdown(
            '<div class="nav-text-links">'
            '<a class="nav-text-link" href="?page=About" target="_self">About</a>'
            '<a class="nav-text-link" href="?page=Contact" target="_self">Contact</a>'
            '</div>',
            unsafe_allow_html=True,
        )
        if user:
            if cols[2].button(f"@{user['username']} · Sign out", key="header_signout", use_container_width=True):
                sign_out()
        else:
            if cols[2].button("Sign in", key="header_signin", type="primary", use_container_width=True):
                login_dialog()


def render_footer() -> None:
    footer_html = """
    <div class="site-footer">
      <div>Project Intelligence · Built for the IBM AI Builders Challenge · AI-assisted teamwork and decision support</div>
      <div class="footer-links">
        <a class="footer-text-link" href="?page=Home" target="_self">Home</a>
        <a class="footer-text-link" href="?page=About" target="_self">About</a>
        <a class="footer-text-link" href="?page=Contact" target="_self">Contact</a>
      </div>
    </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)


render_app_header()

# Standalone informational pages preserve the shared header and footer.
if st.session_state.page == "About":
    st.title("About Project Intelligence")
    st.write(
        "Project Intelligence is a collaborative project-memory and decision-support system. "
        "It converts meeting notes and project updates into structured decisions, actions, "
        "open questions, searchable context, and shared work briefs."
    )
    st.markdown("### Why it exists")
    st.write(
        "Teams often lose important context across meetings, documents, and changing plans. "
        "This prototype keeps that context connected so collaborators can understand what was "
        "decided, what remains unresolved, and what should happen next."
    )
    st.markdown("### Challenge theme")
    st.write("IBM AI Builders Challenge — Wildcard: Intelligent Systems for the Future of Work.")
    if st.button("Return to home", type="primary"):
        go_to("Home")
    render_footer()
    st.stop()

if st.session_state.page == "Contact":
    st.title("Contact the developer")
    st.write("Project Intelligence was developed by **Merve Turan** as a hackathon prototype.")

    st.markdown(
        """
        ### Connect

        - **GitHub:** [github.com/mervturan](https://github.com/mervturan)
        - **LinkedIn:** [Merve Turan](https://www.linkedin.com/in/merve-turan-a12504227/)
        - **Email:** [21mervet@gmail.com](mailto:21mervet@gmail.com)
        - **Live demo:** [project-intelligence.streamlit.app](https://project-intelligence.streamlit.app/)
        """
    )

    if st.button("Return to home", type="primary"):
        go_to("Home")
    render_footer()
    st.stop()

# -----------------------------------------------------------------------------
# Home
# -----------------------------------------------------------------------------
if st.session_state.page == "Home":
    st.markdown(
        """
        <style>
          [data-testid="stSidebar"], [data-testid="collapsedControl"] { display:none !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <section class="home-hero">
          <div class="home-title">🧠 Project Intelligence</div>
          <div class="home-subtitle">A collaborative project memory that turns meetings and updates into decisions, actions, and clear next steps.</div>
          <div class="scroll-cue">Scroll to create, open, or discover a project<br>↓</div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    for key, template in (
        ("project_created_name", 'Project “{}” was created successfully.'),
        ("rename_success", 'Project renamed to “{}”.'),
        ("delete_success", 'Project “{}” was deleted.'),
        ("login_success", 'Welcome, {}.'),
    ):
        value = st.session_state.pop(key, None)
        if value:
            st.success(template.format(value), icon="✅")

    user = get_user(current_user_id()) if current_user_id() else None
    if user:
        st.markdown(f"### Welcome, {html.escape(user['display_name'])}")
        st.caption(f"Signed in as @{user['username']} · Demo collaboration mode")
    else:
        st.markdown("### Continue as a guest or sign in")
        st.caption("Sign in to create private projects, invite collaborators, and request access to public projects.")
        sign_cols = st.columns([1.4, 1, 1.4])
        if sign_cols[1].button("Sign in", key="home_signin", type="primary", use_container_width=True):
            login_dialog()

    st.divider()
    with st.container(border=True):
        st.markdown("## Create a new project")
        if not user:
            st.info("Sign in first to create and manage a project.")
        else:
            with st.form("create_project_form", clear_on_submit=True):
                c1, c2 = st.columns([1, 1.4])
                with c1:
                    new_name = st.text_input("Project name", placeholder="e.g., Product Launch")
                    visibility = st.radio("Visibility", ["Private", "Public"], horizontal=True)
                with c2:
                    new_objective = st.text_area("Objective", placeholder="What outcome is the team working toward?", height=118)
                submitted = st.form_submit_button("Create project", type="primary", use_container_width=True)
            if submitted:
                if not new_name.strip():
                    st.error("Enter a project name.")
                else:
                    new_id = create_project(
                        new_name.strip(),
                        new_objective.strip(),
                        owner_id=int(user["id"]),
                        visibility=visibility.lower(),
                    )
                    if new_id == 0:
                        st.error("You already have a project with that name.")
                    else:
                        st.session_state.project_created_name = new_name.strip()
                        st.session_state.selected_project_id = None
                        go_to("Home")

    st.markdown("## My projects")
    my_projects = list_projects(current_user_id()) if user else []
    if not my_projects:
        st.info("No personal or shared projects yet.")
    else:
        cols = st.columns(3)
        for index, project in enumerate(my_projects):
            pid = int(project["id"])
            with cols[index % 3]:
                with st.container(border=True):
                    top_left, top_right = st.columns([5, 1])
                    with top_left:
                        if st.button(f"📁 {project['name']}", key=f"open_{pid}", use_container_width=True):
                            choose_project(pid)
                    with top_right:
                        if st.button("★" if int(project.get("starred") or 0) else "☆", key=f"star_{pid}", use_container_width=True):
                            toggle_project_star(pid)
                            st.rerun()
                    st.caption(project.get("objective") or "No objective added yet.")
                    owner_label = "You" if project.get("owner_id") == current_user_id() else project.get("owner_name") or "Legacy project"
                    st.markdown(f'<span class="access-pill">{html.escape(project.get("visibility", "private").title())}</span> &nbsp; Owner: {html.escape(owner_label)}', unsafe_allow_html=True)
                    if project.get("owner_id") == current_user_id():
                        edit, delete = st.columns(2)
                        if edit.button("Rename", key=f"home_rename_{pid}", use_container_width=True):
                            rename_dialog(pid)
                        if delete.button("Delete", key=f"home_delete_{pid}", use_container_width=True):
                            delete_dialog(pid)

    if user:
        st.markdown("## Discover public projects")
        discovery_query = st.text_input("Search by project, objective, or owner", placeholder="Search public teamwork projects")
        public_projects = discover_public_projects(int(user["id"]), discovery_query)
        if not public_projects:
            st.caption("No matching public projects are available.")
        else:
            for project in public_projects:
                with st.container(border=True):
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        st.markdown(f"#### {project['name']}")
                        st.write(project.get("objective") or "No objective provided.")
                        st.caption(f"Owner: {project.get('owner_name') or 'Unknown'}")
                    with c2:
                        status = project.get("request_status")
                        if status == "pending":
                            st.button("Requested", disabled=True, key=f"requested_{project['id']}", use_container_width=True)
                        elif st.button("Request to collaborate", key=f"request_{project['id']}", use_container_width=True):
                            request_collaboration(int(project["id"]), int(user["id"]))
                            st.success("Collaboration request sent.")
                            st.rerun()
    render_footer()
    st.stop()

# -----------------------------------------------------------------------------
# Project workspace
# -----------------------------------------------------------------------------
if st.session_state.selected_project_id is None:
    go_to("Home")

project = get_project(int(st.session_state.selected_project_id))
user = get_user(current_user_id()) if current_user_id() else None
is_owner = user_is_owner(int(project["id"]), current_user_id())

with st.sidebar:
    st.markdown('<div class="sidebar-brand">🧠 Project Intelligence</div>', unsafe_allow_html=True)
    if user:
        st.caption(f"Signed in as @{user['username']}")
        if st.button("Sign out", key="sidebar_signout", use_container_width=True):
            sign_out()
    else:
        if st.button("Sign in", key="sidebar_signin", type="primary", use_container_width=True):
            login_dialog()
    if st.button("🏠 Home", use_container_width=True):
        go_to("Home")
    st.divider()
    accessible_projects = list_projects(current_user_id())
    ids = [int(item["id"]) for item in accessible_projects]
    names = {int(item["id"]): item["name"] for item in accessible_projects}
    if ids:
        selected_index = ids.index(int(project["id"])) if int(project["id"]) in ids else 0
        selected = st.selectbox("Current project", ids, index=selected_index, format_func=lambda pid: names[pid])
        if int(selected) != int(project["id"]):
            choose_project(int(selected))
    st.caption("Collapse this navigation using the arrow above.")

# Reliable native project title: heading-like, clickable, and mobile-safe.
with st.container(key="project_title_bar"):
    title_cols = st.columns([8, .65, .65, .65, .65])
    with title_cols[0]:
        if st.button(
            project["name"],
            key="project_title_dashboard",
            help="Return to the project dashboard",
        ):
            go_to("Dashboard")
    if title_cols[1].button("★" if int(project.get("starred") or 0) else "☆", key="project_header_star", help="Star project", use_container_width=True):
        toggle_project_star(int(project["id"]))
        st.rerun()
    if is_owner and title_cols[2].button("✎", key="project_header_rename", help="Rename project", use_container_width=True):
        rename_dialog(int(project["id"]))
    if is_owner and title_cols[3].button("🎯", key="project_header_objective", help="Edit project objective", use_container_width=True):
        objective_dialog(int(project["id"]))
    if is_owner and title_cols[4].button("🗑", key="project_header_delete", help="Delete project", use_container_width=True):
        delete_dialog(int(project["id"]))

st.markdown(
    f'<div class="project-objective">{html.escape(project.get("objective") or "No objective added yet.")} · '
    f'{html.escape(project.get("visibility", "private").title())} project</div>',
    unsafe_allow_html=True,
)
if st.session_state.pop("objective_success", False):
    st.success("Project objective updated.", icon="✅")

with st.container(key="workspace_nav"):
    nav_cols = st.columns(len(PROJECT_PAGES))
    for column, (page_name, icon) in zip(nav_cols, PROJECT_PAGES.items()):
        if column.button(
            f"{icon} {page_name}",
            key=f"nav_{page_name}",
            type="primary" if st.session_state.page == page_name else "secondary",
            use_container_width=True,
        ):
            go_to(page_name)
st.divider()

snapshot = project_snapshot(int(project["id"]))

if st.session_state.page == "Dashboard":
    renamed_name = st.session_state.pop("rename_success", None)
    if renamed_name:
        st.success(f'Project renamed to “{renamed_name}”.')
    st.subheader("Project dashboard")
    metrics = st.columns(4)
    cards = [
        ("📝 Notes", len(snapshot["notes"]), "Notes"),
        ("✅ Decisions", len(snapshot["decisions"]), "Decisions"),
        ("📋 Open actions", len(snapshot["actions"]), "Actions"),
        ("❓ Open questions", len(snapshot["open_questions"]), "Questions"),
    ]
    for col, (label, value, view) in zip(metrics, cards):
        with col:
            with st.container(border=True):
                st.markdown(f"#### {label}")
                st.markdown(f"# {value}")
                if st.button(f"View {view.lower()} →", key=f"metric_{view}", use_container_width=True):
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

elif st.session_state.page == "New note":
    st.subheader("Add a meeting note or project update")
    if st.session_state.pop("note_saved", False):
        intelligence = st.session_state.get("last_saved_intelligence", {})
        st.success("Meeting note processed and added to the shared project memory.")
        r1, r2, r3 = st.columns(3)
        r1.metric("Decisions", len(intelligence.get("decisions", [])))
        r2.metric("Actions", len(intelligence.get("actions", [])))
        r3.metric("Questions", len(intelligence.get("open_questions", [])))
        if st.button("📊 Take me to the project dashboard", type="primary", use_container_width=True):
            go_to("Dashboard")
    with st.form("add_note_form", clear_on_submit=True):
        source = st.text_input("Note title or source", value="Meeting notes")
        note_text = st.text_area("Note", height=280, placeholder="Paste a meeting transcript, project update, or decision log.")
        submitted = st.form_submit_button("Analyse and save", type="primary", use_container_width=True)
    if submitted:
        if not note_text.strip():
            st.error("Add some note text first.")
        else:
            intelligence = extract_note_intelligence(note_text)
            add_note(int(project["id"]), source.strip() or "Note", note_text.strip(), intelligence)
            st.session_state.last_saved_intelligence = intelligence
            st.session_state.generated_brief = None
            st.session_state.note_saved = True
            go_to("New note")

elif st.session_state.page == "Knowledge base":
    st.subheader("Shared project knowledge base")
    cols = st.columns(4)
    for col, view in zip(cols, MEMORY_VIEWS):
        if col.button(view, key=f"memory_{view}", use_container_width=True, type="primary" if st.session_state.memory_view == view else "secondary"):
            st.session_state.memory_view = view
            st.rerun()
    st.divider()
    view = st.session_state.memory_view
    if view == "Notes":
        updated_name = st.session_state.pop("note_updated_name", None)
        deleted_name = st.session_state.pop("note_deleted_name", None)
        if updated_name:
            st.success(f'“{updated_name}” was updated. Project memory has been recalculated.', icon="✅")
        if deleted_name:
            st.success(f'“{deleted_name}” was deleted. Project memory now reflects the remaining notes.', icon="✅")
        if snapshot["notes"]:
            for note in reversed(snapshot["notes"]):
                with st.expander(f"{note['source']} · {note['created_at']}"):
                    st.write(note["content"])
                    st.markdown("**Extracted summary**")
                    st.write(note["intelligence"].get("summary") or "No summary extracted.")
                    st.markdown("**Manage note**")
                    edit_col, delete_col = st.columns(2)
                    if edit_col.button("✏️ Edit note", key=f"edit_note_{note['id']}", use_container_width=True):
                        edit_note_dialog(note)
                    if delete_col.button("🗑️ Delete note", key=f"delete_note_{note['id']}", use_container_width=True):
                        delete_note_dialog(note)
        else:
            st.info("No notes have been added yet.")
    else:
        data_map = {"Decisions": snapshot["decisions"], "Actions": snapshot["actions"], "Questions": snapshot["open_questions"]}
        items = data_map[view]
        if items:
            for idx, item in enumerate(items, 1):
                st.write(f"**{idx}.** {item}")
        else:
            st.info(f"No {view.lower()} have been extracted yet.")

elif st.session_state.page == "Ask AI":
    st.subheader("Ask Project Intelligence")
    question = st.text_input("Question", placeholder="What changed after the latest meeting?")
    if st.button("Ask", type="primary"):
        if not question.strip():
            st.error("Enter a question.")
        else:
            result = answer_project_question(int(project["id"]), question.strip())
            st.markdown("### Answer")
            st.write(result["answer"])
            if result.get("sources"):
                st.markdown("### Supporting notes")
                for source in result["sources"]:
                    with st.expander(source.get("source", "Note")):
                        st.write(source.get("content", ""))

elif st.session_state.page == "Work brief":
    st.subheader("Project work brief")
    if st.button("Generate current brief", type="primary"):
        st.session_state.generated_brief = generate_work_brief(int(project["id"]))
    if st.session_state.get("generated_brief"):
        st.markdown(st.session_state.generated_brief)
    else:
        st.info("Generate a shared overview of decisions, actions, questions, and the recommended next step.")

elif st.session_state.page == "Team":
    st.subheader("Team and collaboration")
    owner_name = project.get("owner_name") or "Legacy project"
    st.markdown(f"**Owner:** {html.escape(owner_name)}")
    visibility_index = 1 if project.get("visibility") == "public" else 0
    if is_owner:
        visibility = st.radio(
            "Project visibility",
            ["Private", "Public"],
            index=visibility_index,
            horizontal=True,
            help="Public projects can be discovered by signed-in users, who may request to collaborate.",
        )
        if visibility.lower() != project.get("visibility"):
            set_project_visibility(int(project["id"]), visibility.lower())
            st.rerun()

        st.markdown("### Add a collaborator")
        query = st.text_input("Search users by name or username", placeholder="e.g., sam or @sam")
        if query.strip():
            matches = search_users(query, exclude_user_id=current_user_id())
            existing_ids = {int(member["id"]) for member in list_project_members(int(project["id"]))}
            for match in matches:
                if int(match["id"]) in existing_ids:
                    continue
                c1, c2 = st.columns([4, 1])
                c1.write(f"**{match['display_name']}** · @{match['username']}")
                if c2.button("Add", key=f"add_member_{match['id']}", use_container_width=True):
                    add_project_member(int(project["id"]), int(match["id"]))
                    st.success(f"Added {match['display_name']} as an editor.")
                    st.rerun()

        requests = list_collaboration_requests(int(project["id"]))
        st.markdown("### Collaboration requests")
        if not requests:
            st.caption("No pending requests.")
        for request in requests:
            c1, c2, c3 = st.columns([4, 1, 1])
            c1.write(f"**{request['display_name']}** · @{request['username']}")
            if c2.button("Approve", key=f"approve_{request['id']}", use_container_width=True):
                resolve_collaboration_request(int(request["id"]), True)
                st.rerun()
            if c3.button("Decline", key=f"decline_{request['id']}", use_container_width=True):
                resolve_collaboration_request(int(request["id"]), False)
                st.rerun()

    st.markdown("### Current collaborators")
    members = list_project_members(int(project["id"]))
    if not members:
        st.caption("No collaborators yet.")
    for member in members:
        c1, c2 = st.columns([5, 1])
        c1.write(f"**{member['display_name']}** · @{member['username']} · {member['role'].title()}")
        if is_owner and c2.button("Remove", key=f"remove_{member['id']}", use_container_width=True):
            remove_project_member(int(project["id"]), int(member["id"]))
            st.rerun()

    if not is_owner:
        st.info("You are collaborating on this project. The owner controls visibility and membership.")

render_footer()