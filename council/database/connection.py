"""
Database connection and initialization — mirrors Brian's pattern.
"""
import sqlite3
import os
import uuid
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

from .schema import SCHEMA_SQL, SCHEMA_VERSION, get_schema_version_sql


class Database:
    """SQLite database manager for Council"""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            home = Path.home()
            council_dir = home / ".council"
            council_dir.mkdir(exist_ok=True, parents=True)
            db_path = str(council_dir / "council.db")
        else:
            db_file = Path(db_path)
            db_file.parent.mkdir(exist_ok=True, parents=True)

        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        if self._connection is None:
            self._connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                isolation_level=None,
            )
            self._connection.execute("PRAGMA foreign_keys = ON")
            self._connection.row_factory = sqlite3.Row
        return self._connection

    def initialize(self):
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
        )

        if cursor.fetchone() is None:
            print(f"Initializing new Council database at {self.db_path}")
            cursor.executescript(SCHEMA_SQL)
            cursor.execute(get_schema_version_sql())
            conn.commit()
            self._seed_default_council()
            self._seed_default_community()
            print("Database initialized successfully!")
        else:
            cursor.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
            result = cursor.fetchone()
            current_version = result[0] if result else 0
            if current_version < SCHEMA_VERSION:
                print(f"Migrating database from v{current_version} to v{SCHEMA_VERSION}")
                self._migrate(current_version, SCHEMA_VERSION)

    def _seed_default_council(self):
        """Create a default hemicycle with empty seats."""
        import uuid, math

        conn = self.connect()
        cursor = conn.cursor()

        # Create 5 rows of seats in a hemicycle
        rows_config = [7, 9, 11, 13, 15]  # seats per row, inner to outer
        center_x, center_y = 500.0, 500.0
        base_radius = 150.0
        row_gap = 50.0

        for row_idx, num_seats in enumerate(rows_config):
            radius = base_radius + row_idx * row_gap
            for pos in range(num_seats):
                angle = math.pi * (pos + 0.5) / num_seats  # 0..π hemicycle
                x = center_x + radius * math.cos(math.pi - angle)
                y = center_y - radius * math.sin(angle)
                seat_id = str(uuid.uuid4())
                label = f"{chr(65 + row_idx)}-{pos + 1}"
                cursor.execute(
                    "INSERT INTO seats (id, row, position, label, x, y) VALUES (?, ?, ?, ?, ?, ?)",
                    (seat_id, row_idx, pos, label, round(x, 2), round(y, 2)),
                )

        conn.commit()
        total = sum(rows_config)
        print(f"  ✓ Seeded {total} seats across {len(rows_config)} rows")

    def _seed_default_community(self):
        """Seed the 60 default community members."""
        import json as _json

        conn = self.connect()
        cursor = conn.cursor()

        # Check if already seeded
        cursor.execute("SELECT COUNT(*) as cnt FROM community_members")
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"  ✓ Community already has {count} members, skipping seed")
            return

        from ..data.default_members import DEFAULT_COMMUNITY_MEMBERS

        for m in DEFAULT_COMMUNITY_MEMBERS:
            member_id = str(uuid.uuid4())
            cursor.execute(
                """INSERT INTO community_members
                   (id, name, cohort, age, profession, background, passions,
                    core_values, communication_style, perspective_summary, is_custom, is_active)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    member_id,
                    m["name"],
                    m["cohort"],
                    m.get("age", 35),
                    m.get("profession", ""),
                    m.get("background", ""),
                    _json.dumps(m.get("passions", [])),
                    _json.dumps(m.get("core_values", [])),
                    m.get("communication_style", ""),
                    m.get("perspective_summary", ""),
                    False,  # is_custom
                    True,   # is_active
                ),
            )

        conn.commit()
        print(f"  ✓ Seeded {len(DEFAULT_COMMUNITY_MEMBERS)} community members across 6 cohorts")

    def _migrate(self, from_version: int, to_version: int):
        """Run migrations from from_version to to_version."""
        from .migrations import get_migrations

        conn = self.connect()
        cursor = conn.cursor()

        migrations = get_migrations()
        for version, sql in migrations:
            if version > from_version and version <= to_version:
                print(f"  Running migration v{version}...")
                cursor.executescript(sql)

        cursor.execute(get_schema_version_sql())
        conn.commit()

        # Seed community members after migration
        if from_version < 2 <= to_version:
            self._seed_default_community()

        print(f"Migration complete: v{from_version} → v{to_version}")

    @contextmanager
    def transaction(self):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("BEGIN")
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e

    def execute(self, query: str, params: tuple = ()):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor

    def fetchone(self, query: str, params: tuple = ()):
        cursor = self.execute(query, params)
        return cursor.fetchone()

    def fetchall(self, query: str, params: tuple = ()):
        cursor = self.execute(query, params)
        return cursor.fetchall()

    def close(self):
        if self._connection:
            self._connection.close()
            self._connection = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
