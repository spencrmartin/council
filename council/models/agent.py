"""
Agent model — represents an AI agent that occupies a seat in the council.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum
import uuid


class AgentRole(str, Enum):
    """Roles an agent can play in the council"""
    SPEAKER = "speaker"          # Orchestrator / leader
    MINISTER = "minister"        # Domain specialist
    DELEGATE = "delegate"        # General-purpose worker
    OBSERVER = "observer"        # Read-only / monitoring
    AUDITOR = "auditor"          # Compliance / review


class AgentStatus(str, Enum):
    """Operational status of an agent"""
    ACTIVE = "active"
    IDLE = "idle"
    SUSPENDED = "suspended"
    OFFLINE = "offline"


@dataclass
class Agent:
    """An AI agent that occupies a seat in the council"""

    name: str
    role: AgentRole = AgentRole.DELEGATE
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: Optional[str] = None
    model_provider: Optional[str] = None   # e.g. "anthropic", "openai"
    model_name: Optional[str] = None       # e.g. "claude-sonnet-4", "gpt-4o"
    icon: str = "bot"                     # Lucide icon name
    color: str = "#6366f1"                 # Hex colour for seat highlight
    status: AgentStatus = AgentStatus.IDLE
    seat_id: Optional[str] = None          # FK → seats.id
    capabilities: Optional[str] = None     # JSON list of capability tags
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role.value if isinstance(self.role, AgentRole) else self.role,
            "description": self.description,
            "model_provider": self.model_provider,
            "model_name": self.model_name,
            "icon": self.icon,
            "color": self.color,
            "status": self.status.value if isinstance(self.status, AgentStatus) else self.status,
            "seat_id": self.seat_id,
            "capabilities": self.capabilities,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_db_row(cls, row: dict) -> "Agent":
        return cls(
            id=row["id"],
            name=row["name"],
            role=AgentRole(row["role"]) if row.get("role") else AgentRole.DELEGATE,
            description=row.get("description"),
            model_provider=row.get("model_provider"),
            model_name=row.get("model_name"),
            icon=row.get("icon", "bot"),
            color=row.get("color", "#6366f1"),
            status=AgentStatus(row["status"]) if row.get("status") else AgentStatus.IDLE,
            seat_id=row.get("seat_id"),
            capabilities=row.get("capabilities"),
            created_at=datetime.fromisoformat(row["created_at"]) if row.get("created_at") else None,
            updated_at=datetime.fromisoformat(row["updated_at"]) if row.get("updated_at") else None,
        )
