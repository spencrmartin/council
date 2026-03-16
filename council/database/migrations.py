"""
Database migrations for Council.
"""

MIGRATION_V2_COMMUNITY = """
-- Community members
CREATE TABLE IF NOT EXISTS community_members (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    cohort TEXT NOT NULL DEFAULT 'builders',
    age INTEGER DEFAULT 35,
    profession TEXT DEFAULT '',
    background TEXT DEFAULT '',
    passions TEXT DEFAULT '[]',
    core_values TEXT DEFAULT '[]',
    communication_style TEXT DEFAULT '',
    perspective_summary TEXT DEFAULT '',
    is_custom BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS focus_groups (
    id TEXT PRIMARY KEY,
    topic TEXT NOT NULL,
    method TEXT NOT NULL DEFAULT 'diverse',
    size INTEGER DEFAULT 8,
    discussion_id TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    synthesis TEXT DEFAULT '',
    cohort_filter TEXT,
    passion_filter TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (discussion_id) REFERENCES discussions(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS focus_group_members (
    focus_group_id TEXT NOT NULL,
    member_id TEXT NOT NULL,
    PRIMARY KEY (focus_group_id, member_id),
    FOREIGN KEY (focus_group_id) REFERENCES focus_groups(id) ON DELETE CASCADE,
    FOREIGN KEY (member_id) REFERENCES community_members(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS member_responses (
    id TEXT PRIMARY KEY,
    member_id TEXT NOT NULL,
    member_name TEXT NOT NULL,
    focus_group_id TEXT,
    poll_id TEXT,
    position TEXT DEFAULT '',
    sentiment REAL DEFAULT 0.0,
    confidence REAL DEFAULT 0.5,
    key_concern TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (member_id) REFERENCES community_members(id) ON DELETE CASCADE,
    FOREIGN KEY (focus_group_id) REFERENCES focus_groups(id) ON DELETE CASCADE,
    FOREIGN KEY (poll_id) REFERENCES community_polls(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS community_polls (
    id TEXT PRIMARY KEY,
    question TEXT NOT NULL,
    discussion_id TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    support_pct REAL DEFAULT 0.0,
    oppose_pct REAL DEFAULT 0.0,
    neutral_pct REAL DEFAULT 0.0,
    top_concerns TEXT DEFAULT '[]',
    top_endorsements TEXT DEFAULT '[]',
    synthesis TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (discussion_id) REFERENCES discussions(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS poll_members (
    poll_id TEXT NOT NULL,
    member_id TEXT NOT NULL,
    PRIMARY KEY (poll_id, member_id),
    FOREIGN KEY (poll_id) REFERENCES community_polls(id) ON DELETE CASCADE,
    FOREIGN KEY (member_id) REFERENCES community_members(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_community_members_cohort ON community_members(cohort);
CREATE INDEX IF NOT EXISTS idx_community_members_active ON community_members(is_active);
CREATE INDEX IF NOT EXISTS idx_community_members_custom ON community_members(is_custom);
CREATE INDEX IF NOT EXISTS idx_focus_groups_status ON focus_groups(status);
CREATE INDEX IF NOT EXISTS idx_focus_groups_discussion ON focus_groups(discussion_id);
CREATE INDEX IF NOT EXISTS idx_member_responses_focus_group ON member_responses(focus_group_id);
CREATE INDEX IF NOT EXISTS idx_member_responses_poll ON member_responses(poll_id);
CREATE INDEX IF NOT EXISTS idx_member_responses_member ON member_responses(member_id);
CREATE INDEX IF NOT EXISTS idx_community_polls_status ON community_polls(status);
CREATE INDEX IF NOT EXISTS idx_community_polls_discussion ON community_polls(discussion_id);

CREATE TRIGGER IF NOT EXISTS update_community_members_timestamp
AFTER UPDATE ON community_members
BEGIN
    UPDATE community_members SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
"""


def get_migrations():
    """Return ordered list of (version, sql) migrations."""
    return [
        (2, MIGRATION_V2_COMMUNITY),
    ]
