"""
Region model — a named group of seats with defined input/output responsibilities.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum
import uuid


class RegionType(str, Enum):
    """How the region was created"""
    MANUAL = "manual"          # User-defined
    AUTO = "auto"              # System-generated from clustering
    COMMITTEE = "committee"    # Formal committee structure


@dataclass
class Region:
    """A named group of council seats with I/O responsibilities"""

    name: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: Optional[str] = None
    color: str = "#8b5cf6"
    region_type: RegionType = RegionType.MANUAL
    is_visible: bool = True
    arc_start_deg: Optional[float] = None   # Start angle in hemicycle (degrees)
    arc_end_deg: Optional[float] = None     # End angle in hemicycle (degrees)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Computed / joined
    seat_ids: List[str] = field(default_factory=list)
    input_ids: List[str] = field(default_factory=list)
    output_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "color": self.color,
            "region_type": self.region_type.value if isinstance(self.region_type, RegionType) else self.region_type,
            "is_visible": self.is_visible,
            "arc_start_deg": self.arc_start_deg,
            "arc_end_deg": self.arc_end_deg,
            "seat_count": len(self.seat_ids),
            "seat_ids": self.seat_ids,
            "input_ids": self.input_ids,
            "output_ids": self.output_ids,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_db_row(
        cls,
        row: dict,
        seat_ids: List[str] = None,
        input_ids: List[str] = None,
        output_ids: List[str] = None,
    ) -> "Region":
        return cls(
            id=row["id"],
            name=row["name"],
            description=row.get("description"),
            color=row.get("color", "#8b5cf6"),
            region_type=RegionType(row["region_type"]) if row.get("region_type") else RegionType.MANUAL,
            is_visible=bool(row.get("is_visible", True)),
            arc_start_deg=row.get("arc_start_deg"),
            arc_end_deg=row.get("arc_end_deg"),
            seat_ids=seat_ids or [],
            input_ids=input_ids or [],
            output_ids=output_ids or [],
            created_at=datetime.fromisoformat(row["created_at"]) if row.get("created_at") else None,
            updated_at=datetime.fromisoformat(row["updated_at"]) if row.get("updated_at") else None,
        )
