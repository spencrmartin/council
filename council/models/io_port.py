"""
IOPort model — an input or output that a region is responsible for.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum
import uuid


class IODirection(str, Enum):
    INPUT = "input"
    OUTPUT = "output"


@dataclass
class IOPort:
    """A named input or output channel assigned to a region"""

    name: str
    direction: IODirection
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: Optional[str] = None
    region_id: Optional[str] = None        # FK → regions.id
    data_type: Optional[str] = None        # e.g. "text", "json", "image", "event"
    schema_json: Optional[str] = None      # Optional JSON Schema for validation
    color: str = "#10b981"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "direction": self.direction.value if isinstance(self.direction, IODirection) else self.direction,
            "description": self.description,
            "region_id": self.region_id,
            "data_type": self.data_type,
            "schema_json": self.schema_json,
            "color": self.color,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_db_row(cls, row: dict) -> "IOPort":
        return cls(
            id=row["id"],
            name=row["name"],
            direction=IODirection(row["direction"]) if row.get("direction") else IODirection.INPUT,
            description=row.get("description"),
            region_id=row.get("region_id"),
            data_type=row.get("data_type"),
            schema_json=row.get("schema_json"),
            color=row.get("color", "#10b981"),
            created_at=datetime.fromisoformat(row["created_at"]) if row.get("created_at") else None,
            updated_at=datetime.fromisoformat(row["updated_at"]) if row.get("updated_at") else None,
        )
