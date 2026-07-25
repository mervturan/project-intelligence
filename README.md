# ContextFlow MVP

ContextFlow is an AI-assisted project-memory and decision-support prototype. It converts scattered notes into structured decisions, action items, unresolved questions, searchable context, and a prioritised work brief.

## Challenge fit

**IBM AI Builders Challenge -  Wildcard: Intelligent Systems for the Future of Work**

ContextFlow demonstrates how AI can transform disconnected work notes into an outcome-driven project memory that helps users plan, decide, and execute.

## MVP features

- Create separate project workspaces
- Paste meeting notes or project updates
- Extract summaries, decisions, actions, deadlines, and open questions
- Store persistent project memory in SQLite
- Ask questions using lightweight local retrieval
- Generate a current project brief and recommended next step
- Run without paid API credentials

The repository uses a deterministic local extraction layer so judges can run it immediately. The service boundary is intentionally modular so IBM Granite or watsonx can replace the starter implementation.

## Architecture

```text
Streamlit UI
    ↓
Note ingestion
    ↓
Structured extraction service
    ↓
SQLite project memory
    ↓
Local retrieval / future vector search
    ↓
Question answering + work brief
```

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL printed by Streamlit.

## Run tests

```bash
pytest
```

## Suggested three-minute demo

1. Create an `MSc Dissertation` project.
2. Add the three examples in `data/sample_notes.md` one at a time.
3. Show the extracted decisions and actions.
4. Ask: `What decisions have we made about datasets?`
5. Generate the work brief.
6. Explain that Granite/watsonx will replace the local starter extractor for richer reasoning.

## IBM Bob usage log

TODO: Document your actual use of IBM Bob here before submission. Examples:

- Planned the repository architecture and MVP scope
- Generated and reviewed service modules
- Debugged Streamlit state and SQLite behaviour
- Added tests and improved error handling
- Refined README and deployment instructions

## Next implementation steps

- Add IBM Granite/watsonx structured JSON extraction
- Add embeddings and FAISS/Chroma semantic retrieval
- Detect changed or superseded decisions
- Add task completion and deadline status
- Support PDF and transcript upload
- Add source citations to generated answers
- Deploy on Streamlit Community Cloud or Hugging Face Spaces

## Responsible AI

ContextFlow is a decision-support prototype, not an autonomous decision-maker. Users should verify generated tasks, deadlines, and recommendations against the original source notes. The interface should preserve evidence links and allow corrections before information becomes part of project memory.

## License

MIT
