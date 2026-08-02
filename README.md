# Project Intelligence

> A collaborative project-memory and decision-support platform that transforms meetings and updates into structured decisions, actions, open questions, searchable context, and shared work briefs.

**Live demo:** https://project-intelligence.streamlit.app/

## IBM AI Builders Challenge 2026

**Selected theme:** Wildcard Challenge — Intelligent Systems for the Future of Work

## Problem statement

Teams generate important information across meetings, project updates, and changing plans. Decisions, ownership, deadlines, and unresolved questions become fragmented, which makes collaboration slower and causes valuable context to be lost.

## Solution description

Project Intelligence creates a shared project workspace where users can capture notes, maintain project memory, collaborate with teammates, ask questions about earlier work, and generate a current project brief. Projects may be private or publicly discoverable, and public projects can receive collaboration requests.

## Current features

- Responsive Home, About, Contact, and project workspace pages
- Demo sign-in and user-specific workspaces
- Private/public projects and collaboration requests
- Add/remove project collaborators
- Create, rename, star, delete, and reorder projects
- Edit project objectives
- Add, edit, and delete meeting notes
- Automatic recalculation of decisions, actions, questions, dashboard counts, Q&A context, and work briefs after note changes
- Shared project dashboard and knowledge base
- Local retrieval-based project Q&A
- Current work-brief generation
- Persistent SQLite storage for the prototype

## AI approach and architecture

```text
Collaborative project workspace
        ↓
Meeting-note and update ingestion
        ↓
Structured extraction service
        ↓
SQLite project memory
        ↓
Retrieval and context assembly
        ↓
Question answering and work briefs
```

The current implementation includes a deterministic local extraction layer so the complete workflow can run without paid credentials. The service boundary is modular so IBM Granite or watsonx can replace the starter extraction and reasoning logic.

## How IBM Bob was used

Before submission, replace or expand this section with the exact activities completed using IBM Bob, such as:

- Planning the repository architecture and MVP scope
- Generating and reviewing service modules
- Debugging Streamlit state and SQLite behaviour
- Improving responsive navigation and project workflows
- Adding tests and error handling
- Refining documentation and deployment configuration

## Run locally

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

## Before final submission

- Connect IBM Granite or watsonx
- Replace demo authentication with production authentication if continuing beyond the hackathon
- Move persistence from local SQLite to a hosted database for durable cloud collaboration
- Add your public GitHub, LinkedIn, and contact email to the Contact page
- Add the final public repository URL
- Record and publish the three-minute demo video

## Responsible AI

Project Intelligence is a decision-support system, not an autonomous decision-maker. Users should verify generated decisions, deadlines, tasks, and recommendations against the original notes. The interface preserves source notes and supports corrections through note editing and deletion.

## License

MIT
