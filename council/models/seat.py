"""
Seat model — a position in the hemicycle layout.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class Seat:
    """A physical seat in the council hemicycle"""

    row: int                               # Row index (0 = front / inner arc)
    position: int                          # Position within the row (0 = leftmost)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    label: Optional[str] = None            # Optional human-readable label e.g. "A-12"
    region_id: Optional[str] = None        # FK → regions.id
    agent_id: Optional[str] = None         # FK → agents.id  (nullable = empty seat)
    x: Optional[float] = None              # Computed x for rendering
    y: Optional[float] = None              # Computed y for rendering
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "row": self.row,
            "position": self.position,
            "label": self.label,
            "region_id": self.region_id,
            "agent_id": self.agent_id,
            "x": self.x,
            "y": self.y,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_db_row(cls, row: dict) -> "Seat":
        return cls(
            id=row["id"],
            row=row["row"],
            position=row["position"],
            label=row.get("label"),
            region_id=row.get("region_id"),
            agent_id=row.get("agent_id"),
            x=row.get("x"),
            y=row.get("y"),
            created_at=datetime.fromisoformat(row["created_at"]) if row.get("created_at") else None,
            updated_at=datetime.fromisoformat(row["updated_at"]) if row.get("updated_at") else None,
        )
