# -*- coding: utf-8 -*-
# ================================================================
# VIDEOFACTORY — SQLITE STATEFUL WORKFLOW & API KEY ROTATOR
# Implements Phase 1: Stateful Resiliency & Auditability
# ================================================================

import sqlite3
import json
import time
from pathlib import Path

DB_PATH = Path("output/videofactory.db")

def get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 1. Projects Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                project_id TEXT PRIMARY KEY,
                title TEXT,
                niche TEXT,
                aspect_ratio TEXT,
                status TEXT,
                current_step TEXT,
                audio_path TEXT,
                output_path TEXT,
                created_at REAL,
                updated_at REAL
            )
        """)
        
        # 2. Workflow States Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT,
                state_name TEXT,
                payload_json TEXT,
                timestamp REAL,
                FOREIGN KEY(project_id) REFERENCES projects(project_id)
            )
        """)
        
        # 3. Transcripts Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transcripts (
                project_id TEXT PRIMARY KEY,
                transcript_json TEXT,
                approved_by_human INTEGER DEFAULT 0,
                updated_at REAL,
                FOREIGN KEY(project_id) REFERENCES projects(project_id)
            )
        """)
        
        # 4. Key Rotation Log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS key_rotations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_name TEXT,
                key_index INTEGER,
                rotated_reason TEXT,
                timestamp REAL
            )
        """)

        # 5. Topic History (Deduplication Protection)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS topics_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT UNIQUE,
                niche TEXT,
                created_at REAL
            )
        """)
        
        conn.commit()

def record_topic(topic: str, niche: str = "gospel"):
    """Records a generated script topic into SQLite to prevent repetition."""
    if not topic or not topic.strip():
        return
    clean_topic = topic.strip().lower()
    with get_db() as conn:
        conn.execute("""
            INSERT INTO topics_history (topic, niche, created_at)
            VALUES (?, ?, ?)
            ON CONFLICT(topic) DO UPDATE SET created_at=?
        """, (clean_topic, niche, time.time(), time.time()))

def is_topic_recent(topic: str, niche: str = "gospel", limit: int = 50) -> bool:
    """Checks if a topic or similar wording has been generated recently."""
    if not topic:
        return False
    clean_topic = topic.strip().lower()
    with get_db() as conn:
        rows = conn.execute("SELECT topic FROM topics_history WHERE niche=? ORDER BY created_at DESC LIMIT ?", (niche, limit)).fetchall()
        for r in rows:
            used = r["topic"]
            if clean_topic in used or used in clean_topic:
                return True
    return False

def get_used_topics(niche: str = "gospel", limit: int = 100) -> list:
    """Returns a list of all recently generated topics for a given niche."""
    with get_db() as conn:
        rows = conn.execute("SELECT topic FROM topics_history WHERE niche=? ORDER BY created_at DESC LIMIT ?", (niche, limit)).fetchall()
        return [r["topic"] for r in rows]

class ProjectStateManager:
    """Manages state transitions and persistent recovery for VideoFactory jobs."""
    
    def __init__(self, project_id: str, title: str = "Untitled Project", niche: str = "gospel", aspect_ratio: str = "9:16"):
        init_db()
        self.project_id = project_id
        self._ensure_project(title, niche, aspect_ratio)

    def _ensure_project(self, title, niche, aspect_ratio):
        now = time.time()
        with get_db() as conn:
            conn.execute("""
                INSERT INTO projects (project_id, title, niche, aspect_ratio, status, current_step, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'INITIALIZED', 'INIT', ?, ?)
                ON CONFLICT(project_id) DO UPDATE SET updated_at=?
            """, (self.project_id, title, niche, aspect_ratio, now, now, now))

    def update_state(self, state_name: str, payload: dict = None):
        now = time.time()
        payload_str = json.dumps(payload or {}, ensure_ascii=False)
        with get_db() as conn:
            conn.execute("""
                UPDATE projects SET status=?, current_step=?, updated_at=? WHERE project_id=?
            """, (state_name, state_name, now, self.project_id))
            
            conn.execute("""
                INSERT INTO workflow_states (project_id, state_name, payload_json, timestamp)
                VALUES (?, ?, ?, ?)
            """, (self.project_id, state_name, payload_str, now))

    def save_transcript(self, transcript_data: dict, approved: bool = False):
        now = time.time()
        json_str = json.dumps(transcript_data, ensure_ascii=False)
        with get_db() as conn:
            conn.execute("""
                INSERT INTO transcripts (project_id, transcript_json, approved_by_human, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(project_id) DO UPDATE SET transcript_json=?, approved_by_human=?, updated_at=?
            """, (self.project_id, json_str, 1 if approved else 0, now, json_str, 1 if approved else 0, now))

    def get_transcript(self):
        with get_db() as conn:
            row = conn.execute("SELECT * FROM transcripts WHERE project_id=?", (self.project_id,)).fetchone()
            if row:
                return {
                    "transcript": json.loads(row["transcript_json"]),
                    "approved": bool(row["approved_by_human"]),
                    "updated_at": row["updated_at"]
                }
        return None

    def get_current_status(self):
        with get_db() as conn:
            row = conn.execute("SELECT * FROM projects WHERE project_id=?", (self.project_id,)).fetchone()
            if row:
                return dict(row)
        return None

def log_key_rotation(service_name: str, key_index: int, reason: str = "HTTP 429 Rate Limit"):
    init_db()
    with get_db() as conn:
        conn.execute("""
            INSERT INTO key_rotations (service_name, key_index, rotated_reason, timestamp)
            VALUES (?, ?, ?, ?)
        """, (service_name, key_index, reason, time.time()))

# Initialize DB on module import
init_db()
