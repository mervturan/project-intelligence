# Project Intelligence

> **An AI-powered project memory and decision intelligence platform that transforms notes, meetings, and documents into actionable knowledge, tracked decisions, and prioritized next steps.**

🚀 **Live Demo:** https://project-intelligence.streamlit.app/

---

# IBM AI Builders Challenge 2026

**Challenge Theme:** Wildcard Challenge – Intelligent Systems for the Future of Work

---

# Problem Statement

Modern teams generate large amounts of information through meetings, documents, chat messages, and project notes. While this information is valuable, it quickly becomes fragmented across different sources, making it difficult to remember previous decisions, track action items, understand project history, and identify the next steps.

As projects grow, teams spend increasing amounts of time searching for information instead of acting on it.

Project Intelligence addresses this problem by transforming unstructured project knowledge into a searchable, structured, and continuously evolving project memory.

---

# Solution Description

Project Intelligence is an AI-powered project memory and decision intelligence platform.

Instead of simply summarizing notes, it continuously organizes project knowledge by extracting:

- Decisions
- Action items
- Deadlines
- Open questions
- Project summaries

The system stores this information as persistent project memory, allowing users to search previous discussions, understand why decisions were made, and generate AI-assisted project briefs with recommended next actions.

---

# Features

- 📂 Project workspaces
- 📝 Note and meeting capture
- 🧠 Structured information extraction
- 💾 Persistent project memory
- 🔎 Project knowledge search
- 💬 Natural language question answering
- 📋 AI-generated work briefs
- ⚡ Decision and action tracking

---

# AI Approach & Architecture

Current MVP Architecture

```text
                  User Notes
                       │
                       ▼
               Streamlit Interface
                       │
                       ▼
           Structured Information Extraction
                       │
                       ▼
            SQLite Project Memory Database
                       │
                       ▼
      Retrieval & Context Assembly Layer
                       │
                       ▼
      Question Answering / Work Brief Generator
```

Current MVP uses a lightweight rule-based extraction pipeline to demonstrate the complete workflow without requiring external AI services.

The architecture is intentionally modular so that IBM Granite and watsonx can replace the extraction and reasoning modules with minimal changes.

---

# Selected Challenge Theme

**IBM AI Builders Challenge 2026**

**Wildcard Challenge — Intelligent Systems for the Future of Work**

Project Intelligence aligns with the challenge by demonstrating how AI can help individuals and teams:

- organize project knowledge
- improve decision-making
- reduce repetitive work
- maintain long-term project memory
- transform disconnected information into actionable outcomes

---

# How IBM Bob Was Used

IBM Bob was used throughout the software development lifecycle, including:

- brainstorming the MVP scope
- planning the application architecture
- generating and refining code
- debugging Python and Streamlit components
- improving the user interface
- reviewing and optimizing implementation
- assisting with documentation

---

# Running Locally

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt

streamlit run app.py
```

---

# Demo Workflow

1. Create a project.
2. Add meeting notes.
3. View extracted decisions and actions.
4. Ask questions about previous meetings.
5. Generate the current project brief.

---

# Roadmap

Future versions will include:

- IBM Granite structured extraction
- watsonx integration
- Semantic search using FAISS/Chroma
- PDF, DOCX and transcript ingestion
- Decision evolution tracking
- Task completion monitoring
- Source citations
- Team collaboration
- Calendar integration
- Slack/Teams integration

---

# Responsible AI

Project Intelligence is designed as a decision-support system.

Users remain responsible for validating generated recommendations, deadlines, and action items. The platform should always provide traceability back to the original project notes and allow users to review or correct extracted information.

---

# License

MIT