"""
Repository classes — CRUD operations for all Council entities.
"""
import uuid
import json
from typing import Optional, List

from .connection import Database
from ..models.agent import Agent, AgentRole, AgentStatus
from ..models.seat import Seat
from ..models.region import Region, RegionType
from ..models.io_port import IOPort, IODirection
from ..models.constitution import Constitution
from ..models.discussion import Discussion, DiscussionMessage, DiscussionStatus, MessageType


# ── Agent Repository ─────────────────────────────────────────────────────────

class AgentRepository:
    def __init__(self, db: Database):
        self.db = db

    def list_all(self) -> List[Agent]:
        rows = self.db.fetchall("SELECT * FROM agents ORDER BY name")
        return [Agent.from_db_row(dict(r)) for r in rows]

    def get(self, agent_id: str) -> Optional[Agent]:
        row = self.db.fetchone("SELECT * FROM agents WHERE id = ?", (agent_id,))
        return Agent.from_db_row(dict(row)) if row else None

    def create(self, agent: Agent) -> Agent:
        if not agent.id:
            agent.id = str(uuid.uuid4())
        self.db.execute(
            """INSERT INTO agents (id, name, role, description, model_provider, model_name,
               icon, color, status, seat_id, capabilities)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                agent.id, agent.name,
                agent.role.value if isinstance(agent.role, AgentRole) else agent.role,
                agent.description, agent.model_provider, agent.model_name,
                agent.icon, agent.color,
                agent.status.value if isinstance(agent.status, AgentStatus) else agent.status,
                agent.seat_id, agent.capabilities,
            ),
        )
        return self.get(agent.id)

    def update(self, agent_id: str, **kwargs) -> Optional[Agent]:
        allowed = {
            "name", "role", "description", "model_provider", "model_name",
            "icon", "color", "status", "seat_id", "capabilities",
        }
        fields = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
        if not fields:
            return self.get(agent_id)
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [agent_id]
        self.db.execute(f"UPDATE agents SET {set_clause} WHERE id = ?", tuple(values))
        return self.get(agent_id)

    def delete(self, agent_id: str) -> bool:
        # Unlink from seat first
        self.db.execute("UPDATE seats SET agent_id = NULL WHERE agent_id = ?", (agent_id,))
        cursor = self.db.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
        return cursor.rowcount > 0

    def assign_seat(self, agent_id: str, seat_id: str) -> Optional[Agent]:
        """Assign an agent to a seat (clears previous occupant)."""
        # Clear any existing agent from target seat
        self.db.execute("UPDATE agents SET seat_id = NULL WHERE seat_id = ?", (seat_id,))
        self.db.execute("UPDATE seats SET agent_id = NULL WHERE id = ?", (seat_id,))
        # Clear agent's previous seat
        agent = self.get(agent_id)
        if agent and agent.seat_id:
            self.db.execute("UPDATE seats SET agent_id = NULL WHERE id = ?", (agent.seat_id,))
        # Assign
        self.db.execute("UPDATE agents SET seat_id = ? WHERE id = ?", (seat_id, agent_id))
        self.db.execute("UPDATE seats SET agent_id = ? WHERE id = ?", (agent_id, seat_id))
        return self.get(agent_id)

    def unseat(self, agent_id: str) -> Optional[Agent]:
        """Remove an agent from their seat."""
        agent = self.get(agent_id)
        if agent and agent.seat_id:
            self.db.execute("UPDATE seats SET agent_id = NULL WHERE id = ?", (agent.seat_id,))
        self.db.execute("UPDATE agents SET seat_id = NULL WHERE id = ?", (agent_id,))
        return self.get(agent_id)


# ── Seat Repository ──────────────────────────────────────────────────────────

class SeatRepository:
    def __init__(self, db: Database):
        self.db = db

    def list_all(self) -> List[Seat]:
        rows = self.db.fetchall("SELECT * FROM seats ORDER BY row, position")
        return [Seat.from_db_row(dict(r)) for r in rows]

    def get(self, seat_id: str) -> Optional[Seat]:
        row = self.db.fetchone("SELECT * FROM seats WHERE id = ?", (seat_id,))
        return Seat.from_db_row(dict(row)) if row else None

    def get_by_region(self, region_id: str) -> List[Seat]:
        rows = self.db.fetchall(
            "SELECT * FROM seats WHERE region_id = ? ORDER BY row, position",
            (region_id,),
        )
        return [Seat.from_db_row(dict(r)) for r in rows]

    def update(self, seat_id: str, **kwargs) -> Optional[Seat]:
        allowed = {"label", "region_id", "agent_id", "x", "y"}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return self.get(seat_id)
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [seat_id]
        self.db.execute(f"UPDATE seats SET {set_clause} WHERE id = ?", tuple(values))
        return self.get(seat_id)

    def assign_region(self, seat_ids: List[str], region_id: Optional[str]) -> int:
        """Assign a list of seats to a region (or None to unassign)."""
        count = 0
        for sid in seat_ids:
            self.db.execute("UPDATE seats SET region_id = ? WHERE id = ?", (region_id, sid))
            count += 1
        return count

    def get_empty(self) -> List[Seat]:
        rows = self.db.fetchall(
            "SELECT * FROM seats WHERE agent_id IS NULL ORDER BY row, position"
        )
        return [Seat.from_db_row(dict(r)) for r in rows]


# ── Region Repository ────────────────────────────────────────────────────────

class RegionRepository:
    def __init__(self, db: Database):
        self.db = db

    def list_all(self) -> List[Region]:
        rows = self.db.fetchall("SELECT * FROM regions ORDER BY name")
        regions = []
        for r in rows:
            rd = dict(r)
            seat_ids = [
                s["id"]
                for s in self.db.fetchall(
                    "SELECT id FROM seats WHERE region_id = ?", (rd["id"],)
                )
            ]
            input_ids = [
                p["id"]
                for p in self.db.fetchall(
                    "SELECT id FROM io_ports WHERE region_id = ? AND direction = 'input'",
                    (rd["id"],),
                )
            ]
            output_ids = [
                p["id"]
                for p in self.db.fetchall(
                    "SELECT id FROM io_ports WHERE region_id = ? AND direction = 'output'",
                    (rd["id"],),
                )
            ]
            regions.append(Region.from_db_row(rd, seat_ids, input_ids, output_ids))
        return regions

    def get(self, region_id: str) -> Optional[Region]:
        row = self.db.fetchone("SELECT * FROM regions WHERE id = ?", (region_id,))
        if not row:
            return None
        rd = dict(row)
        seat_ids = [
            s["id"]
            for s in self.db.fetchall(
                "SELECT id FROM seats WHERE region_id = ?", (rd["id"],)
            )
        ]
        input_ids = [
            p["id"]
            for p in self.db.fetchall(
                "SELECT id FROM io_ports WHERE region_id = ? AND direction = 'input'",
                (rd["id"],),
            )
        ]
        output_ids = [
            p["id"]
            for p in self.db.fetchall(
                "SELECT id FROM io_ports WHERE region_id = ? AND direction = 'output'",
                (rd["id"],),
            )
        ]
        return Region.from_db_row(rd, seat_ids, input_ids, output_ids)

    def create(self, region: Region) -> Region:
        if not region.id:
            region.id = str(uuid.uuid4())
        self.db.execute(
            """INSERT INTO regions (id, name, description, color, region_type, is_visible,
               arc_start_deg, arc_end_deg)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                region.id, region.name, region.description, region.color,
                region.region_type.value if isinstance(region.region_type, RegionType) else region.region_type,
                region.is_visible, region.arc_start_deg, region.arc_end_deg,
            ),
        )
        return self.get(region.id)

    def update(self, region_id: str, **kwargs) -> Optional[Region]:
        allowed = {"name", "description", "color", "region_type", "is_visible", "arc_start_deg", "arc_end_deg"}
        fields = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
        if not fields:
            return self.get(region_id)
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [region_id]
        self.db.execute(f"UPDATE regions SET {set_clause} WHERE id = ?", tuple(values))
        return self.get(region_id)

    def delete(self, region_id: str) -> bool:
        # Unlink seats and io_ports
        self.db.execute("UPDATE seats SET region_id = NULL WHERE region_id = ?", (region_id,))
        self.db.execute("UPDATE io_ports SET region_id = NULL WHERE region_id = ?", (region_id,))
        cursor = self.db.execute("DELETE FROM regions WHERE id = ?", (region_id,))
        return cursor.rowcount > 0


# ── IOPort Repository ────────────────────────────────────────────────────────

class IOPortRepository:
    def __init__(self, db: Database):
        self.db = db

    def list_all(self, region_id: Optional[str] = None, direction: Optional[str] = None) -> List[IOPort]:
        query = "SELECT * FROM io_ports WHERE 1=1"
        params = []
        if region_id:
            query += " AND region_id = ?"
            params.append(region_id)
        if direction:
            query += " AND direction = ?"
            params.append(direction)
        query += " ORDER BY direction, name"
        rows = self.db.fetchall(query, tuple(params))
        return [IOPort.from_db_row(dict(r)) for r in rows]

    def get(self, port_id: str) -> Optional[IOPort]:
        row = self.db.fetchone("SELECT * FROM io_ports WHERE id = ?", (port_id,))
        return IOPort.from_db_row(dict(row)) if row else None

    def create(self, port: IOPort) -> IOPort:
        if not port.id:
            port.id = str(uuid.uuid4())
        self.db.execute(
            """INSERT INTO io_ports (id, name, direction, description, region_id, data_type, schema_json, color)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                port.id, port.name,
                port.direction.value if isinstance(port.direction, IODirection) else port.direction,
                port.description, port.region_id, port.data_type, port.schema_json, port.color,
            ),
        )
        return self.get(port.id)

    def update(self, port_id: str, **kwargs) -> Optional[IOPort]:
        allowed = {"name", "direction", "description", "region_id", "data_type", "schema_json", "color"}
        fields = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
        if not fields:
            return self.get(port_id)
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [port_id]
        self.db.execute(f"UPDATE io_ports SET {set_clause} WHERE id = ?", tuple(values))
        return self.get(port_id)

    def delete(self, port_id: str) -> bool:
        cursor = self.db.execute("DELETE FROM io_ports WHERE id = ?", (port_id,))
        return cursor.rowcount > 0


# ── Constitution Repository ──────────────────────────────────────────────────

class ConstitutionRepository:
    def __init__(self, db: Database):
        self.db = db

    def get_active(self) -> Optional[Constitution]:
        """Get the currently active constitution."""
        row = self.db.fetchone(
            "SELECT * FROM constitutions WHERE is_active = 1 LIMIT 1"
        )
        return Constitution.from_db_row(dict(row)) if row else None

    def get(self, constitution_id: str) -> Optional[Constitution]:
        row = self.db.fetchone(
            "SELECT * FROM constitutions WHERE id = ?", (constitution_id,)
        )
        return Constitution.from_db_row(dict(row)) if row else None

    def list_all(self) -> list:
        """List all constitutions ordered by version descending (newest first)."""
        rows = self.db.fetchall(
            "SELECT * FROM constitutions ORDER BY version DESC"
        )
        return [Constitution.from_db_row(dict(r)) for r in rows]

    def create(self, preamble: str = "", rules: str = "", goals: str = "",
               constraints: str = "", created_by: str = None,
               activate: bool = True) -> Constitution:
        """Create a new constitution version. If activate=True, deactivate all others first."""
        # Determine next version number
        row = self.db.fetchone(
            "SELECT COALESCE(MAX(version), 0) as max_v FROM constitutions"
        )
        next_version = (row["max_v"] if row else 0) + 1

        new_id = str(uuid.uuid4())

        if activate:
            self.db.execute("UPDATE constitutions SET is_active = 0 WHERE is_active = 1")

        self.db.execute(
            """INSERT INTO constitutions (id, version, preamble, rules, goals, constraints, is_active, created_by)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (new_id, next_version, preamble, rules, goals, constraints,
             1 if activate else 0, created_by),
        )
        return self.get(new_id)

    def activate(self, constitution_id: str) -> Optional[Constitution]:
        """Set a constitution as active, deactivating all others."""
        self.db.execute("UPDATE constitutions SET is_active = 0 WHERE is_active = 1")
        self.db.execute("UPDATE constitutions SET is_active = 1 WHERE id = ?", (constitution_id,))
        return self.get(constitution_id)


# ── Discussion Repository ────────────────────────────────────────────────────

class DiscussionRepository:
    def __init__(self, db: Database):
        self.db = db

    def _get_messages(self, discussion_id: str) -> List[DiscussionMessage]:
        rows = self.db.fetchall(
            "SELECT * FROM discussion_messages WHERE discussion_id = ? ORDER BY created_at",
            (discussion_id,),
        )
        return [DiscussionMessage.from_db_row(dict(r)) for r in rows]

    def list_all(self, limit: int = 50) -> List[Discussion]:
        rows = self.db.fetchall(
            "SELECT * FROM discussions ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        discussions = []
        for r in rows:
            d = dict(r)
            msgs = self._get_messages(d["id"])
            discussions.append(Discussion.from_db_row(d, msgs))
        return discussions

    def get(self, discussion_id: str) -> Optional[Discussion]:
        row = self.db.fetchone("SELECT * FROM discussions WHERE id = ?", (discussion_id,))
        if not row:
            return None
        msgs = self._get_messages(discussion_id)
        return Discussion.from_db_row(dict(row), msgs)

    def create(self, topic: str, description: str = None, created_by: str = None) -> Discussion:
        new_id = str(uuid.uuid4())
        self.db.execute(
            "INSERT INTO discussions (id, topic, description, status, created_by) VALUES (?, ?, ?, ?, ?)",
            (new_id, topic, description, "open", created_by),
        )
        return self.get(new_id)

    def add_message(self, discussion_id: str, agent_id: str, agent_name: str,
                    content: str, agent_role: str = None,
                    message_type: str = "statement") -> DiscussionMessage:
        msg_id = str(uuid.uuid4())
        self.db.execute(
            """INSERT INTO discussion_messages
               (id, discussion_id, agent_id, agent_name, agent_role, content, message_type)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (msg_id, discussion_id, agent_id, agent_name, agent_role, content, message_type),
        )
        row = self.db.fetchone("SELECT * FROM discussion_messages WHERE id = ?", (msg_id,))
        return DiscussionMessage.from_db_row(dict(row))

    def update_status(self, discussion_id: str, status: str, conclusion: str = None) -> Optional[Discussion]:
        if conclusion:
            self.db.execute(
                "UPDATE discussions SET status = ?, conclusion = ?, concluded_at = CURRENT_TIMESTAMP WHERE id = ?",
                (status, conclusion, discussion_id),
            )
        else:
            self.db.execute(
                "UPDATE discussions SET status = ? WHERE id = ?",
                (status, discussion_id),
            )
        return self.get(discussion_id)
