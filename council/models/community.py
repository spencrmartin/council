"""
Community member models — the 60-person civic layer of the council.

Community members are diverse personas with unique perspectives, passions,
and communication styles. They can be engaged through focus groups, polls,
town halls, and individual consultations to stress-test council decisions.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum
import uuid
import json


class Cohort(str, Enum):
    """The six cohorts that community members belong to."""
    BUILDERS = "builders"          # Engineers, designers, makers
    OPERATORS = "operators"        # Managers, coordinators, admins
    ADVOCATES = "advocates"        # Activists, ethicists, community organizers
    PRAGMATISTS = "pragmatists"    # Business owners, economists, analysts
    CREATIVES = "creatives"        # Artists, writers, philosophers
    SKEPTICS = "skeptics"          # Researchers, auditors, critics


class FocusGroupMethod(str, Enum):
    """How members are selected for a focus group."""
    RANDOM = "random"              # Random sample of N members
    COHORT = "cohort"              # All from one cohort
    DIVERSE = "diverse"            # One from each cohort (guaranteed spread)
    TARGETED = "targeted"          # Filter by passions/values


class FocusGroupStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"


class PollStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"


@dataclass
class CommunityMember:
    """A community member with a unique perspective and voice."""

    name: str
    cohort: Cohort
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    age: int = 35
    profession: str = ""
    background: str = ""                    # Short bio
    passions: List[str] = field(default_factory=list)
    core_values: List[str] = field(default_factory=list)
    communication_style: str = ""           # e.g. "direct and data-driven"
    perspective_summary: str = ""           # 2-3 sentence worldview distillation
    is_custom: bool = False                 # True if user-created/modified
    is_active: bool = True                  # Can be deactivated without deleting
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "cohort": self.cohort.value if isinstance(self.cohort, Cohort) else self.cohort,
            "age": self.age,
            "profession": self.profession,
            "background": self.background,
            "passions": self.passions,
            "core_values": self.core_values,
            "communication_style": self.communication_style,
            "perspective_summary": self.perspective_summary,
            "is_custom": self.is_custom,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_db_row(cls, row: dict) -> "CommunityMember":
        passions = row.get("passions", "[]")
        if isinstance(passions, str):
            passions = json.loads(passions) if passions else []
        core_values = row.get("core_values", "[]")
        if isinstance(core_values, str):
            core_values = json.loads(core_values) if core_values else []
        return cls(
            id=row["id"],
            name=row["name"],
            cohort=Cohort(row["cohort"]) if row.get("cohort") else Cohort.BUILDERS,
            age=row.get("age", 35),
            profession=row.get("profession", ""),
            background=row.get("background", ""),
            passions=passions,
            core_values=core_values,
            communication_style=row.get("communication_style", ""),
            perspective_summary=row.get("perspective_summary", ""),
            is_custom=bool(row.get("is_custom", False)),
            is_active=bool(row.get("is_active", True)),
            created_at=datetime.fromisoformat(row["created_at"]) if row.get("created_at") else None,
            updated_at=datetime.fromisoformat(row["updated_at"]) if row.get("updated_at") else None,
        )

    def build_persona_prompt(self) -> str:
        """Build a system prompt fragment that captures this member's voice."""
        parts = [
            f"You are {self.name}, a {self.age}-year-old {self.profession}.",
        ]
        if self.background:
            parts.append(f"Background: {self.background}")
        if self.passions:
            parts.append(f"You are passionate about: {', '.join(self.passions)}.")
        if self.core_values:
            parts.append(f"Your core values: {', '.join(self.core_values)}.")
        if self.communication_style:
            parts.append(f"Communication style: {self.communication_style}.")
        if self.perspective_summary:
            parts.append(f"Worldview: {self.perspective_summary}")
        return "\n".join(parts)


@dataclass
class MemberResponse:
    """A single community member's response in a focus group or poll."""

    member_id: str
    member_name: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    focus_group_id: Optional[str] = None
    poll_id: Optional[str] = None
    position: str = ""                      # Their take / response text
    sentiment: float = 0.0                  # -1.0 to 1.0
    confidence: float = 0.5                 # 0.0 to 1.0
    key_concern: str = ""                   # One-liner summary
    created_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "member_id": self.member_id,
            "member_name": self.member_name,
            "focus_group_id": self.focus_group_id,
            "poll_id": self.poll_id,
            "position": self.position,
            "sentiment": self.sentiment,
            "confidence": self.confidence,
            "key_concern": self.key_concern,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_db_row(cls, row: dict) -> "MemberResponse":
        return cls(
            id=row["id"],
            member_id=row["member_id"],
            member_name=row.get("member_name", ""),
            focus_group_id=row.get("focus_group_id"),
            poll_id=row.get("poll_id"),
            position=row.get("position", ""),
            sentiment=float(row.get("sentiment", 0.0)),
            confidence=float(row.get("confidence", 0.5)),
            key_concern=row.get("key_concern", ""),
            created_at=datetime.fromisoformat(row["created_at"]) if row.get("created_at") else None,
        )


@dataclass
class FocusGroup:
    """A convened group of community members discussing a topic."""

    topic: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    method: FocusGroupMethod = FocusGroupMethod.DIVERSE
    size: int = 8
    discussion_id: Optional[str] = None     # Links to council discussion
    status: FocusGroupStatus = FocusGroupStatus.PENDING
    member_ids: List[str] = field(default_factory=list)
    responses: List[MemberResponse] = field(default_factory=list)
    synthesis: str = ""                     # AI-generated summary
    cohort_filter: Optional[str] = None     # For cohort method
    passion_filter: Optional[str] = None    # For targeted method
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "topic": self.topic,
            "method": self.method.value if isinstance(self.method, FocusGroupMethod) else self.method,
            "size": self.size,
            "discussion_id": self.discussion_id,
            "status": self.status.value if isinstance(self.status, FocusGroupStatus) else self.status,
            "member_ids": self.member_ids,
            "responses": [r.to_dict() for r in self.responses],
            "synthesis": self.synthesis,
            "cohort_filter": self.cohort_filter,
            "passion_filter": self.passion_filter,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "response_count": len(self.responses),
        }

    @classmethod
    def from_db_row(cls, row: dict, member_ids: List[str] = None,
                    responses: List[MemberResponse] = None) -> "FocusGroup":
        return cls(
            id=row["id"],
            topic=row["topic"],
            method=FocusGroupMethod(row["method"]) if row.get("method") else FocusGroupMethod.DIVERSE,
            size=row.get("size", 8),
            discussion_id=row.get("discussion_id"),
            status=FocusGroupStatus(row["status"]) if row.get("status") else FocusGroupStatus.PENDING,
            member_ids=member_ids or [],
            responses=responses or [],
            synthesis=row.get("synthesis", ""),
            cohort_filter=row.get("cohort_filter"),
            passion_filter=row.get("passion_filter"),
            created_at=datetime.fromisoformat(row["created_at"]) if row.get("created_at") else None,
            completed_at=datetime.fromisoformat(row["completed_at"]) if row.get("completed_at") else None,
        )


@dataclass
class CommunityPoll:
    """A poll across community members on a specific question."""

    question: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    discussion_id: Optional[str] = None
    status: PollStatus = PollStatus.PENDING
    member_ids: List[str] = field(default_factory=list)
    responses: List[MemberResponse] = field(default_factory=list)
    # Aggregated results
    support_pct: float = 0.0
    oppose_pct: float = 0.0
    neutral_pct: float = 0.0
    top_concerns: List[str] = field(default_factory=list)
    top_endorsements: List[str] = field(default_factory=list)
    synthesis: str = ""
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "question": self.question,
            "discussion_id": self.discussion_id,
            "status": self.status.value if isinstance(self.status, PollStatus) else self.status,
            "member_count": len(self.member_ids),
            "response_count": len(self.responses),
            "results": {
                "support_pct": self.support_pct,
                "oppose_pct": self.oppose_pct,
                "neutral_pct": self.neutral_pct,
                "top_concerns": self.top_concerns,
                "top_endorsements": self.top_endorsements,
            },
            "synthesis": self.synthesis,
            "responses": [r.to_dict() for r in self.responses],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    @classmethod
    def from_db_row(cls, row: dict, member_ids: List[str] = None,
                    responses: List[MemberResponse] = None) -> "CommunityPoll":
        top_concerns = row.get("top_concerns", "[]")
        if isinstance(top_concerns, str):
            top_concerns = json.loads(top_concerns) if top_concerns else []
        top_endorsements = row.get("top_endorsements", "[]")
        if isinstance(top_endorsements, str):
            top_endorsements = json.loads(top_endorsements) if top_endorsements else []
        return cls(
            id=row["id"],
            question=row["question"],
            discussion_id=row.get("discussion_id"),
            status=PollStatus(row["status"]) if row.get("status") else PollStatus.PENDING,
            member_ids=member_ids or [],
            responses=responses or [],
            support_pct=float(row.get("support_pct", 0.0)),
            oppose_pct=float(row.get("oppose_pct", 0.0)),
            neutral_pct=float(row.get("neutral_pct", 0.0)),
            top_concerns=top_concerns,
            top_endorsements=top_endorsements,
            synthesis=row.get("synthesis", ""),
            created_at=datetime.fromisoformat(row["created_at"]) if row.get("created_at") else None,
            completed_at=datetime.fromisoformat(row["completed_at"]) if row.get("completed_at") else None,
        )
