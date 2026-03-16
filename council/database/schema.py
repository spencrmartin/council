"""
Database schema for Council — Agent Governance Visualization
"""

SCHEMA_VERSION = 2

SCHEMA_SQL = """
-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Regions — named groups of seats with I/O responsibilities
CREATE TABLE IF NOT EXISTS regions (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    color TEXT DEFAULT '#8b5cf6',
    region_type TEXT NOT NULL DEFAULT 'manual',
    is_visible BOOLEAN DEFAULT TRUE,
    arc_start_deg REAL,
    arc_end_deg REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agents — AI agents that occupy seats
CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'delegate',
    description TEXT,
    model_provider TEXT,
    model_name TEXT,
    icon TEXT DEFAULT 'bot',
    color TEXT DEFAULT '#6366f1',
    status TEXT NOT NULL DEFAULT 'idle',
    seat_id TEXT UNIQUE,
    capabilities TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (seat_id) REFERENCES seats(id) ON DELETE SET NULL
);

-- Seats — positions in the hemicycle layout
CREATE TABLE IF NOT EXISTS seats (
    id TEXT PRIMARY KEY,
    row INTEGER NOT NULL,
    position INTEGER NOT NULL,
    label TEXT,
    region_id TEXT,
    agent_id TEXT UNIQUE,
    x REAL,
    y REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (region_id) REFERENCES regions(id) ON DELETE SET NULL,
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE SET NULL,
    UNIQUE(row, position)
);

-- IO Ports — inputs and outputs assigned to regions
CREATE TABLE IF NOT EXISTS io_ports (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    direction TEXT NOT NULL DEFAULT 'input',
    description TEXT,
    region_id TEXT,
    data_type TEXT,
    schema_json TEXT,
    color TEXT DEFAULT '#10b981',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (region_id) REFERENCES regions(id) ON DELETE SET NULL
);

-- Constitutions — versioned governing documents with audit trail
CREATE TABLE IF NOT EXISTS constitutions (
    id TEXT PRIMARY KEY,                 -- UUID
    version INTEGER NOT NULL DEFAULT 1,
    preamble TEXT DEFAULT '',
    rules TEXT DEFAULT '',               -- markdown rules/guidelines
    goals TEXT DEFAULT '',               -- markdown goals/objectives
    constraints TEXT DEFAULT '',          -- markdown constraints/boundaries
    is_active BOOLEAN DEFAULT FALSE,
    created_by TEXT,                      -- user name who created this version
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_constitutions_active ON constitutions(is_active);
CREATE INDEX IF NOT EXISTS idx_constitutions_version ON constitutions(version DESC);

-- Discussions — topics/motions brought before the council
CREATE TABLE IF NOT EXISTS discussions (
    id TEXT PRIMARY KEY,
    topic TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'open',  -- 'open', 'deliberating', 'concluded'
    conclusion TEXT,                       -- final summary/decision
    created_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    concluded_at TIMESTAMP
);

-- Discussion messages — individual agent contributions
CREATE TABLE IF NOT EXISTS discussion_messages (
    id TEXT PRIMARY KEY,
    discussion_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    agent_role TEXT,
    content TEXT NOT NULL,
    message_type TEXT NOT NULL DEFAULT 'statement',  -- 'statement', 'vote_for', 'vote_against', 'abstain', 'question', 'objection'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (discussion_id) REFERENCES discussions(id) ON DELETE CASCADE,
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_discussions_status ON discussions(status);
CREATE INDEX IF NOT EXISTS idx_discussions_created ON discussions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_discussion_messages_discussion ON discussion_messages(discussion_id);
CREATE INDEX IF NOT EXISTS idx_discussion_messages_agent ON discussion_messages(agent_id);

-- ═══════════════════════════════════════════════════════════════════════════
-- Community Members — the 60-person civic layer
-- ═══════════════════════════════════════════════════════════════════════════

-- Community members — diverse personas with unique perspectives
CREATE TABLE IF NOT EXISTS community_members (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    cohort TEXT NOT NULL DEFAULT 'builders',   -- builders, operators, advocates, pragmatists, creatives, skeptics
    age INTEGER DEFAULT 35,
    profession TEXT DEFAULT '',
    background TEXT DEFAULT '',                 -- short bio
    passions TEXT DEFAULT '[]',                 -- JSON array of strings
    core_values TEXT DEFAULT '[]',              -- JSON array of strings
    communication_style TEXT DEFAULT '',
    perspective_summary TEXT DEFAULT '',
    is_custom BOOLEAN DEFAULT FALSE,           -- user-created/modified
    is_active BOOLEAN DEFAULT TRUE,            -- can be deactivated
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Focus groups — convened groups of members discussing a topic
CREATE TABLE IF NOT EXISTS focus_groups (
    id TEXT PRIMARY KEY,
    topic TEXT NOT NULL,
    method TEXT NOT NULL DEFAULT 'diverse',     -- random, cohort, diverse, targeted
    size INTEGER DEFAULT 8,
    discussion_id TEXT,                         -- links to council discussion
    status TEXT NOT NULL DEFAULT 'pending',     -- pending, active, completed
    synthesis TEXT DEFAULT '',                  -- AI-generated summary
    cohort_filter TEXT,                         -- for cohort method
    passion_filter TEXT,                        -- for targeted method
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (discussion_id) REFERENCES discussions(id) ON DELETE SET NULL
);

-- Focus group membership — which members are in which focus group
CREATE TABLE IF NOT EXISTS focus_group_members (
    focus_group_id TEXT NOT NULL,
    member_id TEXT NOT NULL,
    PRIMARY KEY (focus_group_id, member_id),
    FOREIGN KEY (focus_group_id) REFERENCES focus_groups(id) ON DELETE CASCADE,
    FOREIGN KEY (member_id) REFERENCES community_members(id) ON DELETE CASCADE
);

-- Member responses — individual responses in focus groups or polls
CREATE TABLE IF NOT EXISTS member_responses (
    id TEXT PRIMARY KEY,
    member_id TEXT NOT NULL,
    member_name TEXT NOT NULL,
    focus_group_id TEXT,
    poll_id TEXT,
    position TEXT DEFAULT '',                  -- their take / response text
    sentiment REAL DEFAULT 0.0,                -- -1.0 to 1.0
    confidence REAL DEFAULT 0.5,               -- 0.0 to 1.0
    key_concern TEXT DEFAULT '',               -- one-liner summary
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (member_id) REFERENCES community_members(id) ON DELETE CASCADE,
    FOREIGN KEY (focus_group_id) REFERENCES focus_groups(id) ON DELETE CASCADE,
    FOREIGN KEY (poll_id) REFERENCES community_polls(id) ON DELETE CASCADE
);

-- Community polls — quick sentiment checks across members
CREATE TABLE IF NOT EXISTS community_polls (
    id TEXT PRIMARY KEY,
    question TEXT NOT NULL,
    discussion_id TEXT,
    status TEXT NOT NULL DEFAULT 'pending',     -- pending, active, completed
    support_pct REAL DEFAULT 0.0,
    oppose_pct REAL DEFAULT 0.0,
    neutral_pct REAL DEFAULT 0.0,
    top_concerns TEXT DEFAULT '[]',             -- JSON array
    top_endorsements TEXT DEFAULT '[]',         -- JSON array
    synthesis TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (discussion_id) REFERENCES discussions(id) ON DELETE SET NULL
);

-- Poll membership — which members are polled
CREATE TABLE IF NOT EXISTS poll_members (
    poll_id TEXT NOT NULL,
    member_id TEXT NOT NULL,
    PRIMARY KEY (poll_id, member_id),
    FOREIGN KEY (poll_id) REFERENCES community_polls(id) ON DELETE CASCADE,
    FOREIGN KEY (member_id) REFERENCES community_members(id) ON DELETE CASCADE
);

-- Community indexes
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

-- Community triggers
CREATE TRIGGER IF NOT EXISTS update_community_members_timestamp
AFTER UPDATE ON community_members
BEGIN
    UPDATE community_members SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Indexes
CREATE INDEX IF NOT EXISTS idx_agents_role ON agents(role);
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS idx_agents_seat ON agents(seat_id);
CREATE INDEX IF NOT EXISTS idx_seats_region ON seats(region_id);
CREATE INDEX IF NOT EXISTS idx_seats_agent ON seats(agent_id);
CREATE INDEX IF NOT EXISTS idx_seats_row ON seats(row);
CREATE INDEX IF NOT EXISTS idx_io_ports_region ON io_ports(region_id);
CREATE INDEX IF NOT EXISTS idx_io_ports_direction ON io_ports(direction);
CREATE INDEX IF NOT EXISTS idx_regions_type ON regions(region_type);
CREATE INDEX IF NOT EXISTS idx_regions_visible ON regions(is_visible);

-- Triggers for updated_at
CREATE TRIGGER IF NOT EXISTS update_agents_timestamp
AFTER UPDATE ON agents
BEGIN
    UPDATE agents SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_seats_timestamp
AFTER UPDATE ON seats
BEGIN
    UPDATE seats SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_regions_timestamp
AFTER UPDATE ON regions
BEGIN
    UPDATE regions SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_io_ports_timestamp
AFTER UPDATE ON io_ports
BEGIN
    UPDATE io_ports SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;


"""


def get_schema_version_sql():
    return f"INSERT OR REPLACE INTO schema_version (version) VALUES ({SCHEMA_VERSION});"
