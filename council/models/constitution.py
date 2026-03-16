"""
Constitution model — versioned governing documents with audit trail.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class Constitution:
    """A versioned constitution for the council."""

    preamble: str = ""
    rules: str = ""
    goals: str = ""
    constraints: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    version: int = 1
    is_active: bool = False
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "version": self.version,
            "preamble": self.preamble,
            "rules": self.rules,
            "goals": self.goals,
            "constraints": self.constraints,
            "is_active": self.is_active,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_db_row(cls, row: dict) -> "Constitution":
        return cls(
            id=row["id"],
            version=row.get("version", 1),
            preamble=row.get("preamble", ""),
            rules=row.get("rules", ""),
            goals=row.get("goals", ""),
            constraints=row.get("constraints", ""),
            is_active=bool(row.get("is_active", False)),
            created_by=row.get("created_by"),
            created_at=datetime.fromisoformat(row["created_at"]) if row.get("created_at") else None,
        )
