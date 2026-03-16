"""
Database schema for Council — Agent Governance Visualization
"""

SCHEMA_VERSION = 1

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
