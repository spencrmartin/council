"""
Repository classes for Community Members — CRUD + focus group + poll operations.
"""
import uuid
import json
import random
from typing import Optional, List

from .connection import Database
from ..models.community import (
    CommunityMember, Cohort, FocusGroup, FocusGroupMethod, FocusGroupStatus,
    MemberResponse, CommunityPoll, PollStatus,
)


# ── Community Member Repository ──────────────────────────────────────────────

class CommunityMemberRepository:
    def __init__(self, db: Database):
        self.db = db

    def list_all(self, active_only: bool = True) -> List[CommunityMember]:
        if active_only:
            rows = self.db.fetchall(
                "SELECT * FROM community_members WHERE is_active = 1 ORDER BY cohort, name"
            )
        else:
            rows = self.db.fetchall(
                "SELECT * FROM community_members ORDER BY cohort, name"
            )
        return [CommunityMember.from_db_row(dict(r)) for r in rows]

    def get(self, member_id: str) -> Optional[CommunityMember]:
        row = self.db.fetchone("SELECT * FROM community_members WHERE id = ?", (member_id,))
        return CommunityMember.from_db_row(dict(row)) if row else None

    def get_by_cohort(self, cohort: str, active_only: bool = True) -> List[CommunityMember]:
        if active_only:
            rows = self.db.fetchall(
                "SELECT * FROM community_members WHERE cohort = ? AND is_active = 1 ORDER BY name",
                (cohort,),
            )
        else:
            rows = self.db.fetchall(
                "SELECT * FROM community_members WHERE cohort = ? ORDER BY name",
                (cohort,),
            )
        return [CommunityMember.from_db_row(dict(r)) for r in rows]

    def get_by_passion(self, passion: str, active_only: bool = True) -> List[CommunityMember]:
        """Find members whose passions contain the given keyword (case-insensitive)."""
        if active_only:
            rows = self.db.fetchall(
                "SELECT * FROM community_members WHERE is_active = 1 AND LOWER(passions) LIKE ? ORDER BY name",
                (f"%{passion.lower()}%",),
            )
        else:
            rows = self.db.fetchall(
                "SELECT * FROM community_members WHERE LOWER(passions) LIKE ? ORDER BY name",
                (f"%{passion.lower()}%",),
            )
        return [CommunityMember.from_db_row(dict(r)) for r in rows]

    def create(self, member: CommunityMember) -> CommunityMember:
        if not member.id:
            member.id = str(uuid.uuid4())
        self.db.execute(
            """INSERT INTO community_members
               (id, name, cohort, age, profession, background, passions,
                core_values, communication_style, perspective_summary, is_custom, is_active)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                member.id, member.name,
                member.cohort.value if isinstance(member.cohort, Cohort) else member.cohort,
                member.age, member.profession, member.background,
                json.dumps(member.passions), json.dumps(member.core_values),
                member.communication_style, member.perspective_summary,
                member.is_custom, member.is_active,
            ),
        )
        return self.get(member.id)

    def update(self, member_id: str, **kwargs) -> Optional[CommunityMember]:
        allowed = {
            "name", "cohort", "age", "profession", "background",
            "passions", "core_values", "communication_style",
            "perspective_summary", "is_custom", "is_active",
        }
        fields = {}
        for k, v in kwargs.items():
            if k in allowed and v is not None:
                if k in ("passions", "core_values") and isinstance(v, list):
                    fields[k] = json.dumps(v)
                else:
                    fields[k] = v
        if not fields:
            return self.get(member_id)

        # Mark as custom when user modifies a default member
        if "is_custom" not in fields:
            fields["is_custom"] = True

        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [member_id]
        self.db.execute(f"UPDATE community_members SET {set_clause} WHERE id = ?", tuple(values))
        return self.get(member_id)

    def delete(self, member_id: str) -> bool:
        cursor = self.db.execute("DELETE FROM community_members WHERE id = ?", (member_id,))
        return cursor.rowcount > 0

    def reset_defaults(self) -> int:
        """Delete all non-custom members and re-seed defaults. Returns count seeded."""
        self.db.execute("DELETE FROM community_members WHERE is_custom = 0")
        from ..data.default_members import DEFAULT_COMMUNITY_MEMBERS
        count = 0
        for m in DEFAULT_COMMUNITY_MEMBERS:
            member_id = str(uuid.uuid4())
            self.db.execute(
                """INSERT INTO community_members
                   (id, name, cohort, age, profession, background, passions,
                    core_values, communication_style, perspective_summary, is_custom, is_active)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    member_id, m["name"], m["cohort"], m.get("age", 35),
                    m.get("profession", ""), m.get("background", ""),
                    json.dumps(m.get("passions", [])), json.dumps(m.get("core_values", [])),
                    m.get("communication_style", ""), m.get("perspective_summary", ""),
                    False, True,
                ),
            )
            count += 1
        return count

    def select_members(
        self,
        method: str = "diverse",
        size: int = 8,
        cohort_filter: str = None,
        passion_filter: str = None,
    ) -> List[CommunityMember]:
        """Select members using the specified method."""
        all_active = self.list_all(active_only=True)

        if method == "cohort" and cohort_filter:
            pool = [m for m in all_active if (m.cohort.value if isinstance(m.cohort, Cohort) else m.cohort) == cohort_filter]
            return pool[:size] if len(pool) <= size else random.sample(pool, size)

        if method == "targeted" and passion_filter:
            pool = self.get_by_passion(passion_filter)
            if len(pool) <= size:
                return pool
            return random.sample(pool, size)

        if method == "diverse":
            # One from each cohort, then fill remaining randomly
            cohorts = list(Cohort)
            selected = []
            for cohort in cohorts:
                cohort_members = [m for m in all_active if (m.cohort.value if isinstance(m.cohort, Cohort) else m.cohort) == cohort.value]
                if cohort_members:
                    selected.append(random.choice(cohort_members))
            # Fill remaining slots
            remaining = [m for m in all_active if m not in selected]
            slots_left = size - len(selected)
            if slots_left > 0 and remaining:
                selected.extend(random.sample(remaining, min(slots_left, len(remaining))))
            return selected[:size]

        # Random
        if len(all_active) <= size:
            return all_active
        return random.sample(all_active, size)

    def get_stats(self) -> dict:
        """Get community statistics."""
        all_members = self.list_all(active_only=False)
        active = [m for m in all_members if m.is_active]
        custom = [m for m in all_members if m.is_custom]

        cohort_counts = {}
        for cohort in Cohort:
            cohort_counts[cohort.value] = sum(
                1 for m in active
                if (m.cohort.value if isinstance(m.cohort, Cohort) else m.cohort) == cohort.value
            )

        return {
            "total_members": len(all_members),
            "active_members": len(active),
            "custom_members": len(custom),
            "default_members": len(all_members) - len(custom),
            "cohort_counts": cohort_counts,
        }


# ── Focus Group Repository ──────────────────────────────────────────────────

class FocusGroupRepository:
    def __init__(self, db: Database):
        self.db = db

    def _get_member_ids(self, focus_group_id: str) -> List[str]:
        rows = self.db.fetchall(
            "SELECT member_id FROM focus_group_members WHERE focus_group_id = ?",
            (focus_group_id,),
        )
        return [r["member_id"] for r in rows]

    def _get_responses(self, focus_group_id: str) -> List[MemberResponse]:
        rows = self.db.fetchall(
            "SELECT * FROM member_responses WHERE focus_group_id = ? ORDER BY created_at",
            (focus_group_id,),
        )
        return [MemberResponse.from_db_row(dict(r)) for r in rows]

    def list_all(self, limit: int = 50) -> List[FocusGroup]:
        rows = self.db.fetchall(
            "SELECT * FROM focus_groups ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        groups = []
        for r in rows:
            d = dict(r)
            member_ids = self._get_member_ids(d["id"])
            responses = self._get_responses(d["id"])
            groups.append(FocusGroup.from_db_row(d, member_ids, responses))
        return groups

    def get(self, focus_group_id: str) -> Optional[FocusGroup]:
        row = self.db.fetchone("SELECT * FROM focus_groups WHERE id = ?", (focus_group_id,))
        if not row:
            return None
        d = dict(row)
        member_ids = self._get_member_ids(d["id"])
        responses = self._get_responses(d["id"])
        return FocusGroup.from_db_row(d, member_ids, responses)

    def create(
        self,
        topic: str,
        member_ids: List[str],
        method: str = "diverse",
        size: int = 8,
        discussion_id: str = None,
        cohort_filter: str = None,
        passion_filter: str = None,
    ) -> FocusGroup:
        fg_id = str(uuid.uuid4())
        self.db.execute(
            """INSERT INTO focus_groups
               (id, topic, method, size, discussion_id, status, cohort_filter, passion_filter)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (fg_id, topic, method, size, discussion_id, "pending", cohort_filter, passion_filter),
        )
        # Add members
        for mid in member_ids:
            self.db.execute(
                "INSERT OR IGNORE INTO focus_group_members (focus_group_id, member_id) VALUES (?, ?)",
                (fg_id, mid),
            )
        return self.get(fg_id)

    def add_response(
        self,
        focus_group_id: str,
        member_id: str,
        member_name: str,
        position: str,
        sentiment: float = 0.0,
        confidence: float = 0.5,
        key_concern: str = "",
    ) -> MemberResponse:
        resp_id = str(uuid.uuid4())
        self.db.execute(
            """INSERT INTO member_responses
               (id, member_id, member_name, focus_group_id, position, sentiment, confidence, key_concern)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (resp_id, member_id, member_name, focus_group_id, position, sentiment, confidence, key_concern),
        )
        row = self.db.fetchone("SELECT * FROM member_responses WHERE id = ?", (resp_id,))
        return MemberResponse.from_db_row(dict(row))

    def update_status(self, focus_group_id: str, status: str, synthesis: str = None) -> Optional[FocusGroup]:
        if synthesis:
            self.db.execute(
                "UPDATE focus_groups SET status = ?, synthesis = ?, completed_at = CURRENT_TIMESTAMP WHERE id = ?",
                (status, synthesis, focus_group_id),
            )
        else:
            self.db.execute(
                "UPDATE focus_groups SET status = ? WHERE id = ?",
                (status, focus_group_id),
            )
        return self.get(focus_group_id)

    def delete(self, focus_group_id: str) -> bool:
        self.db.execute("DELETE FROM focus_group_members WHERE focus_group_id = ?", (focus_group_id,))
        self.db.execute("DELETE FROM member_responses WHERE focus_group_id = ?", (focus_group_id,))
        cursor = self.db.execute("DELETE FROM focus_groups WHERE id = ?", (focus_group_id,))
        return cursor.rowcount > 0


# ── Community Poll Repository ────────────────────────────────────────────────

class CommunityPollRepository:
    def __init__(self, db: Database):
        self.db = db

    def _get_member_ids(self, poll_id: str) -> List[str]:
        rows = self.db.fetchall(
            "SELECT member_id FROM poll_members WHERE poll_id = ?", (poll_id,)
        )
        return [r["member_id"] for r in rows]

    def _get_responses(self, poll_id: str) -> List[MemberResponse]:
        rows = self.db.fetchall(
            "SELECT * FROM member_responses WHERE poll_id = ? ORDER BY created_at",
            (poll_id,),
        )
        return [MemberResponse.from_db_row(dict(r)) for r in rows]

    def list_all(self, limit: int = 50) -> List[CommunityPoll]:
        rows = self.db.fetchall(
            "SELECT * FROM community_polls ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        polls = []
        for r in rows:
            d = dict(r)
            member_ids = self._get_member_ids(d["id"])
            responses = self._get_responses(d["id"])
            polls.append(CommunityPoll.from_db_row(d, member_ids, responses))
        return polls

    def get(self, poll_id: str) -> Optional[CommunityPoll]:
        row = self.db.fetchone("SELECT * FROM community_polls WHERE id = ?", (poll_id,))
        if not row:
            return None
        d = dict(row)
        member_ids = self._get_member_ids(d["id"])
        responses = self._get_responses(d["id"])
        return CommunityPoll.from_db_row(d, member_ids, responses)

    def create(
        self,
        question: str,
        member_ids: List[str],
        discussion_id: str = None,
    ) -> CommunityPoll:
        poll_id = str(uuid.uuid4())
        self.db.execute(
            "INSERT INTO community_polls (id, question, discussion_id, status) VALUES (?, ?, ?, ?)",
            (poll_id, question, discussion_id, "pending"),
        )
        for mid in member_ids:
            self.db.execute(
                "INSERT OR IGNORE INTO poll_members (poll_id, member_id) VALUES (?, ?)",
                (poll_id, mid),
            )
        return self.get(poll_id)

    def add_response(
        self,
        poll_id: str,
        member_id: str,
        member_name: str,
        position: str,
        sentiment: float = 0.0,
        confidence: float = 0.5,
        key_concern: str = "",
    ) -> MemberResponse:
        resp_id = str(uuid.uuid4())
        self.db.execute(
            """INSERT INTO member_responses
               (id, member_id, member_name, poll_id, position, sentiment, confidence, key_concern)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (resp_id, member_id, member_name, poll_id, position, sentiment, confidence, key_concern),
        )
        row = self.db.fetchone("SELECT * FROM member_responses WHERE id = ?", (resp_id,))
        return MemberResponse.from_db_row(dict(row))

    def update_results(
        self,
        poll_id: str,
        support_pct: float,
        oppose_pct: float,
        neutral_pct: float,
        top_concerns: List[str] = None,
        top_endorsements: List[str] = None,
        synthesis: str = "",
    ) -> Optional[CommunityPoll]:
        self.db.execute(
            """UPDATE community_polls SET
               status = 'completed', support_pct = ?, oppose_pct = ?, neutral_pct = ?,
               top_concerns = ?, top_endorsements = ?, synthesis = ?,
               completed_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (
                support_pct, oppose_pct, neutral_pct,
                json.dumps(top_concerns or []),
                json.dumps(top_endorsements or []),
                synthesis,
                poll_id,
            ),
        )
        return self.get(poll_id)

    def delete(self, poll_id: str) -> bool:
        self.db.execute("DELETE FROM poll_members WHERE poll_id = ?", (poll_id,))
        self.db.execute("DELETE FROM member_responses WHERE poll_id = ?", (poll_id,))
        cursor = self.db.execute("DELETE FROM community_polls WHERE id = ?", (poll_id,))
        return cursor.rowcount > 0
