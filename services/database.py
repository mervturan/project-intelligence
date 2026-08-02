"""SQLite persistence for projects, collaboration, notes, and extracted intelligence."""
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
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _column_names(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                display_name TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                objective TEXT NOT NULL DEFAULT '',
                starred INTEGER NOT NULL DEFAULT 0,
                position INTEGER NOT NULL DEFAULT 0,
                owner_id INTEGER,
                visibility TEXT NOT NULL DEFAULT 'private',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(owner_id) REFERENCES users(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS project_members (
                project_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL DEFAULT 'editor',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(project_id, user_id),
                FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS collaboration_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                requester_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(project_id, requester_id),
                FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY(requester_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                source TEXT NOT NULL,
                content TEXT NOT NULL,
                intelligence_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
            );
            """
        )
        columns = _column_names(conn, "projects")
        migrations = {
            "starred": "ALTER TABLE projects ADD COLUMN starred INTEGER NOT NULL DEFAULT 0",
            "position": "ALTER TABLE projects ADD COLUMN position INTEGER NOT NULL DEFAULT 0",
            "owner_id": "ALTER TABLE projects ADD COLUMN owner_id INTEGER",
            "visibility": "ALTER TABLE projects ADD COLUMN visibility TEXT NOT NULL DEFAULT 'private'",
            "updated_at": "ALTER TABLE projects ADD COLUMN updated_at TEXT",
        }
        for column, sql in migrations.items():
            if column not in columns:
                conn.execute(sql)
        conn.execute("UPDATE projects SET updated_at = created_at WHERE updated_at IS NULL")
        rows = conn.execute("SELECT id, position FROM projects ORDER BY created_at ASC, id ASC").fetchall()
        if rows and all(int(row["position"] or 0) == 0 for row in rows):
            for index, row in enumerate(rows):
                conn.execute("UPDATE projects SET position = ? WHERE id = ?", (index, row["id"]))


def get_or_create_user(username: str, display_name: str = "") -> dict[str, Any]:
    username = username.strip().lower().replace(" ", "_")
    if not username:
        raise ValueError("Username is required")
    display_name = display_name.strip() or username
    with _connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if row:
            return dict(row)
        cursor = conn.execute(
            "INSERT INTO users(username, display_name) VALUES (?, ?)",
            (username, display_name),
        )
        row = conn.execute("SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return dict(row)


def get_user(user_id: int) -> dict[str, Any] | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


def search_users(query: str, exclude_user_id: int | None = None) -> list[dict[str, Any]]:
    term = f"%{query.strip()}%"
    with _connect() as conn:
        sql = "SELECT * FROM users WHERE (username LIKE ? OR display_name LIKE ?)"
        params: list[Any] = [term, term]
        if exclude_user_id is not None:
            sql += " AND id != ?"
            params.append(exclude_user_id)
        sql += " ORDER BY display_name LIMIT 20"
        rows = conn.execute(sql, params).fetchall()
    return [dict(row) for row in rows]


def create_project(name: str, objective: str = "", owner_id: int | None = None, visibility: str = "private") -> int:
    with _connect() as conn:
        if owner_id is not None:
            duplicate = conn.execute(
                "SELECT 1 FROM projects WHERE owner_id = ? AND lower(name) = lower(?)",
                (owner_id, name),
            ).fetchone()
            if duplicate:
                return 0
        next_position = conn.execute(
            "SELECT COALESCE(MAX(position), -1) + 1 AS next_position FROM projects"
        ).fetchone()["next_position"]
        cursor = conn.execute(
            "INSERT INTO projects(name, objective, position, owner_id, visibility) VALUES (?, ?, ?, ?, ?)",
            (name, objective, next_position, owner_id, visibility),
        )
        return int(cursor.lastrowid)


def list_projects(user_id: int | None = None) -> list[dict[str, Any]]:
    with _connect() as conn:
        if user_id is None:
            rows = conn.execute(
                "SELECT p.*, u.display_name AS owner_name FROM projects p LEFT JOIN users u ON u.id=p.owner_id WHERE p.visibility='public' OR p.owner_id IS NULL ORDER BY p.starred DESC, p.position ASC, p.updated_at DESC"
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT DISTINCT p.*, u.display_name AS owner_name,
                    CASE WHEN p.owner_id = ? THEN 'owner' ELSE COALESCE(pm.role, 'viewer') END AS access_role
                FROM projects p
                LEFT JOIN users u ON u.id = p.owner_id
                LEFT JOIN project_members pm ON pm.project_id = p.id AND pm.user_id = ?
                WHERE p.owner_id = ? OR pm.user_id = ? OR p.owner_id IS NULL
                ORDER BY p.starred DESC, p.position ASC, p.updated_at DESC
                """,
                (user_id, user_id, user_id, user_id),
            ).fetchall()
    return [dict(row) for row in rows]


def discover_public_projects(user_id: int, query: str = "") -> list[dict[str, Any]]:
    term = f"%{query.strip()}%"
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT p.*, u.display_name AS owner_name,
                   cr.status AS request_status
            FROM projects p
            LEFT JOIN users u ON u.id = p.owner_id
            LEFT JOIN project_members pm ON pm.project_id=p.id AND pm.user_id=?
            LEFT JOIN collaboration_requests cr ON cr.project_id=p.id AND cr.requester_id=?
            WHERE p.visibility='public' AND p.owner_id != ? AND pm.user_id IS NULL
              AND (p.name LIKE ? OR p.objective LIKE ? OR u.display_name LIKE ?)
            ORDER BY p.updated_at DESC LIMIT 30
            """,
            (user_id, user_id, user_id, term, term, term),
        ).fetchall()
    return [dict(row) for row in rows]


def get_project(project_id: int) -> dict[str, Any]:
    with _connect() as conn:
        row = conn.execute(
            "SELECT p.*, u.display_name AS owner_name FROM projects p LEFT JOIN users u ON u.id=p.owner_id WHERE p.id = ?",
            (project_id,),
        ).fetchone()
    if row is None:
        raise ValueError(f"Project {project_id} does not exist")
    return dict(row)


def user_can_access_project(project_id: int, user_id: int | None) -> bool:
    project = get_project(project_id)
    if project["owner_id"] is None:
        return True
    if user_id is None:
        return project["visibility"] == "public"
    if project["owner_id"] == user_id:
        return True
    with _connect() as conn:
        return conn.execute(
            "SELECT 1 FROM project_members WHERE project_id=? AND user_id=?",
            (project_id, user_id),
        ).fetchone() is not None


def user_is_owner(project_id: int, user_id: int | None) -> bool:
    if user_id is None:
        return False
    return get_project(project_id).get("owner_id") == user_id


def rename_project(project_id: int, new_name: str) -> bool:
    project = get_project(project_id)
    try:
        with _connect() as conn:
            if project.get("owner_id") is not None:
                duplicate = conn.execute(
                    "SELECT 1 FROM projects WHERE owner_id=? AND lower(name)=lower(?) AND id!=?",
                    (project["owner_id"], new_name, project_id),
                ).fetchone()
                if duplicate:
                    return False
            cursor = conn.execute(
                "UPDATE projects SET name=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (new_name, project_id),
            )
            return cursor.rowcount > 0
    except sqlite3.IntegrityError:
        return False



def update_project_objective(project_id: int, objective: str) -> None:
    """Update a project's objective and refresh its modified timestamp."""
    with _connect() as conn:
        conn.execute(
            "UPDATE projects SET objective=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (objective.strip(), project_id),
        )

def delete_project(project_id: int) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))


def toggle_project_star(project_id: int) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE projects SET starred=CASE starred WHEN 1 THEN 0 ELSE 1 END, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (project_id,),
        )


def set_project_visibility(project_id: int, visibility: str) -> None:
    if visibility not in {"private", "public"}:
        raise ValueError("Invalid visibility")
    with _connect() as conn:
        conn.execute(
            "UPDATE projects SET visibility=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (visibility, project_id),
        )


def reorder_projects(project_ids: list[int]) -> None:
    with _connect() as conn:
        existing = {int(row["id"]) for row in conn.execute("SELECT id FROM projects").fetchall()}
        cleaned = [pid for pid in project_ids if pid in existing]
        cleaned.extend(sorted(existing.difference(cleaned)))
        for position, project_id in enumerate(cleaned):
            conn.execute("UPDATE projects SET position=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (position, project_id))


def add_project_member(project_id: int, user_id: int, role: str = "editor") -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO project_members(project_id,user_id,role) VALUES (?,?,?)",
            (project_id, user_id, role),
        )
        conn.execute("UPDATE projects SET updated_at=CURRENT_TIMESTAMP WHERE id=?", (project_id,))


def remove_project_member(project_id: int, user_id: int) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM project_members WHERE project_id=? AND user_id=?", (project_id, user_id))


def list_project_members(project_id: int) -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT u.id, u.username, u.display_name, pm.role, pm.created_at
            FROM project_members pm JOIN users u ON u.id=pm.user_id
            WHERE pm.project_id=? ORDER BY u.display_name
            """,
            (project_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def request_collaboration(project_id: int, requester_id: int) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO collaboration_requests(project_id,requester_id,status) VALUES (?,?,'pending') ON CONFLICT(project_id,requester_id) DO UPDATE SET status='pending', created_at=CURRENT_TIMESTAMP",
            (project_id, requester_id),
        )


def list_collaboration_requests(project_id: int, status: str = "pending") -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT cr.id, cr.project_id, cr.requester_id, cr.status, cr.created_at,
                   u.username, u.display_name
            FROM collaboration_requests cr JOIN users u ON u.id=cr.requester_id
            WHERE cr.project_id=? AND cr.status=? ORDER BY cr.created_at
            """,
            (project_id, status),
        ).fetchall()
    return [dict(row) for row in rows]


def resolve_collaboration_request(request_id: int, approve: bool) -> None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM collaboration_requests WHERE id=?", (request_id,)).fetchone()
        if not row:
            return
        status = "approved" if approve else "declined"
        conn.execute("UPDATE collaboration_requests SET status=? WHERE id=?", (status, request_id))
        if approve:
            conn.execute(
                "INSERT OR IGNORE INTO project_members(project_id,user_id,role) VALUES (?,?,'editor')",
                (row["project_id"], row["requester_id"]),
            )


def add_note(project_id: int, source: str, content: str, intelligence: dict[str, Any]) -> int:
    with _connect() as conn:
        cursor = conn.execute(
            "INSERT INTO notes(project_id,source,content,intelligence_json) VALUES (?,?,?,?)",
            (project_id, source, content, json.dumps(intelligence)),
        )
        conn.execute("UPDATE projects SET updated_at=CURRENT_TIMESTAMP WHERE id=?", (project_id,))
        return int(cursor.lastrowid)



def update_note(note_id: int, source: str, content: str, intelligence: dict[str, Any]) -> None:
    """Update a note and replace its derived intelligence atomically."""
    with _connect() as conn:
        row = conn.execute("SELECT project_id FROM notes WHERE id=?", (note_id,)).fetchone()
        if row is None:
            raise ValueError(f"Note {note_id} does not exist")
        conn.execute(
            "UPDATE notes SET source=?, content=?, intelligence_json=? WHERE id=?",
            (source, content, json.dumps(intelligence), note_id),
        )
        conn.execute(
            "UPDATE projects SET updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (row["project_id"],),
        )


def delete_note(note_id: int) -> None:
    """Delete a note. Project intelligence is derived from remaining notes on demand."""
    with _connect() as conn:
        row = conn.execute("SELECT project_id FROM notes WHERE id=?", (note_id,)).fetchone()
        if row is None:
            return
        conn.execute("DELETE FROM notes WHERE id=?", (note_id,))
        conn.execute(
            "UPDATE projects SET updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (row["project_id"],),
        )

def get_notes(project_id: int) -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM notes WHERE project_id=? ORDER BY created_at ASC,id ASC", (project_id,)).fetchall()
    notes: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["intelligence"] = json.loads(item.pop("intelligence_json"))
        notes.append(item)
    return notes


def project_snapshot(project_id: int) -> dict[str, Any]:
    notes = get_notes(project_id)
    snapshot: dict[str, Any] = {"notes": notes, "decisions": [], "actions": [], "open_questions": [], "summaries": []}
    for note in notes:
        intel = note["intelligence"]
        snapshot["decisions"].extend(intel.get("decisions", []))
        snapshot["actions"].extend(intel.get("actions", []))
        snapshot["open_questions"].extend(intel.get("open_questions", []))
        if intel.get("summary"):
            snapshot["summaries"].append(intel["summary"])
    return snapshot
