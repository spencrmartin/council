"""
Discussion models — topics, messages, and deliberation.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum
import uuid


class DiscussionStatus(str, Enum):
    OPEN = "open"
    DELIBERATING = "deliberating"
    CONCLUDED = "concluded"


class MessageType(str, Enum):
    STATEMENT = "statement"
    VOTE_FOR = "vote_for"
    VOTE_AGAINST = "vote_against"
    ABSTAIN = "abstain"
    QUESTION = "question"
    OBJECTION = "objection"


@dataclass
class DiscussionMessage:
    """A single message from an agent in a discussion."""

    discussion_id: str
    agent_id: str
    agent_name: str
    content: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_role: Optional[str] = None
    message_type: MessageType = MessageType.STATEMENT
    created_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "discussion_id": self.discussion_id,
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "agent_role": self.agent_role,
            "content": self.content,
            "message_type": self.message_type.value if isinstance(self.message_type, MessageType) else self.message_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_db_row(cls, row: dict) -> "DiscussionMessage":
        return cls(
            id=row["id"],
            discussion_id=row["discussion_id"],
            agent_id=row["agent_id"],
            agent_name=row["agent_name"],
            agent_role=row.get("agent_role"),
            content=row["content"],
            message_type=MessageType(row["message_type"]) if row.get("message_type") else MessageType.STATEMENT,
            created_at=datetime.fromisoformat(row["created_at"]) if row.get("created_at") else None,
        )


@dataclass
class Discussion:
    """A topic or motion brought before the council."""

    topic: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: Optional[str] = None
    status: DiscussionStatus = DiscussionStatus.OPEN
    conclusion: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    concluded_at: Optional[datetime] = None
    messages: List[DiscussionMessage] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "topic": self.topic,
            "description": self.description,
            "status": self.status.value if isinstance(self.status, DiscussionStatus) else self.status,
            "conclusion": self.conclusion,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "concluded_at": self.concluded_at.isoformat() if self.concluded_at else None,
            "messages": [m.to_dict() for m in self.messages],
            "message_count": len(self.messages),
        }

    @classmethod
    def from_db_row(cls, row: dict, messages: List[DiscussionMessage] = None) -> "Discussion":
        return cls(
            id=row["id"],
            topic=row["topic"],
            description=row.get("description"),
            status=DiscussionStatus(row["status"]) if row.get("status") else DiscussionStatus.OPEN,
            conclusion=row.get("conclusion"),
            created_by=row.get("created_by"),
            created_at=datetime.fromisoformat(row["created_at"]) if row.get("created_at") else None,
            concluded_at=datetime.fromisoformat(row["concluded_at"]) if row.get("concluded_at") else None,
            messages=messages or [],
        )
