"""SQLite persistence for projects, notes, and extracted intelligence."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "contextflow.db"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                objective TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                source TEXT NOT NULL,
                content TEXT NOT NULL,
                intelligence_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            );
            """
        )


def create_project(name: str, objective: str = "") -> int:
    with _connect() as conn:
        cursor = conn.execute(
            "INSERT OR IGNORE INTO projects(name, objective) VALUES (?, ?)",
            (name, objective),
        )
        return int(cursor.lastrowid or 0)


def list_projects() -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM projects ORDER BY created_at DESC").fetchall()
    return [dict(row) for row in rows]


def get_project(project_id: int) -> dict[str, Any]:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if row is None:
        raise ValueError(f"Project {project_id} does not exist")
    return dict(row)


def add_note(project_id: int, source: str, content: str, intelligence: dict[str, Any]) -> int:
    with _connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO notes(project_id, source, content, intelligence_json)
            VALUES (?, ?, ?, ?)
            """,
            (project_id, source, content, json.dumps(intelligence)),
        )
        return int(cursor.lastrowid)


def get_notes(project_id: int) -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM notes WHERE project_id = ? ORDER BY created_at ASC, id ASC",
            (project_id,),
        ).fetchall()

    notes: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["intelligence"] = json.loads(item.pop("intelligence_json"))
        notes.append(item)
    return notes


def project_snapshot(project_id: int) -> dict[str, Any]:
    notes = get_notes(project_id)
    snapshot: dict[str, Any] = {
        "notes": notes,
        "decisions": [],
        "actions": [],
        "open_questions": [],
        "summaries": [],
    }
    for note in notes:
        intel = note["intelligence"]
        snapshot["decisions"].extend(intel.get("decisions", []))
        snapshot["actions"].extend(intel.get("actions", []))
        snapshot["open_questions"].extend(intel.get("open_questions", []))
        if intel.get("summary"):
            snapshot["summaries"].append(intel["summary"])
    return snapshot
