"""
FastAPI routes for Council backend.
"""
from fastapi import APIRouter, HTTPException
from typing import Optional

router = APIRouter(prefix="/api")

# These will be set by main.py after DB init
agent_repo = None
seat_repo = None
region_repo = None
io_port_repo = None
constitution_repo = None
discussion_repo = None


def init_repos(agents, seats, regions, io_ports, constitution, discussions):
    global agent_repo, seat_repo, region_repo, io_port_repo, constitution_repo, discussion_repo
    agent_repo = agents
    seat_repo = seats
    region_repo = regions
    io_port_repo = io_ports
    constitution_repo = constitution
    discussion_repo = discussions


# ── Council overview ──────────────────────────────────────────────────────

@router.get("/council")
async def get_council():
    """Full council state: all seats, agents, regions, I/O ports, and constitution."""
    seats = [s.to_dict() for s in seat_repo.list_all()]
    agents = [a.to_dict() for a in agent_repo.list_all()]
    regions = [r.to_dict() for r in region_repo.list_all()]
    io_ports = [p.to_dict() for p in io_port_repo.list_all()]
    active_constitution = constitution_repo.get_active()
    constitution = active_constitution.to_dict() if active_constitution else None

    # Build a lookup for agent on each seat
    agent_map = {a["seat_id"]: a for a in agents if a.get("seat_id")}
    for seat in seats:
        seat["agent"] = agent_map.get(seat["id"])

    return {
        "seats": seats,
        "agents": agents,
        "regions": regions,
        "io_ports": io_ports,
        "constitution": constitution,
        "stats": {
            "total_seats": len(seats),
            "occupied_seats": sum(1 for s in seats if s.get("agent_id")),
            "total_agents": len(agents),
            "total_regions": len(regions),
            "total_inputs": sum(1 for p in io_ports if p["direction"] == "input"),
            "total_outputs": sum(1 for p in io_ports if p["direction"] == "output"),
        },
    }


# ── Agents ───────────────────────────────────────────────────────────────────

@router.get("/agents")
async def list_agents():
    return [a.to_dict() for a in agent_repo.list_all()]


@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    agent = agent_repo.get(agent_id)
    if not agent:
        raise HTTPException(404, "Agent not found")
    return agent.to_dict()


@router.post("/agents")
async def create_agent(body: dict):
    from ..models.agent import Agent, AgentRole
    agent = Agent(
        name=body["name"],
        role=AgentRole(body.get("role", "delegate")),
        description=body.get("description"),
        model_provider=body.get("model_provider"),
        model_name=body.get("model_name"),
        icon=body.get("icon", "bot"),
        color=body.get("color", "#6366f1"),
    )
    created = agent_repo.create(agent)
    return created.to_dict()


@router.put("/agents/{agent_id}")
async def update_agent(agent_id: str, body: dict):
    updated = agent_repo.update(agent_id, **body)
    if not updated:
        raise HTTPException(404, "Agent not found")
    return updated.to_dict()


@router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str):
    if not agent_repo.delete(agent_id):
        raise HTTPException(404, "Agent not found")
    return {"ok": True}


@router.post("/agents/{agent_id}/assign/{seat_id}")
async def assign_agent_seat(agent_id: str, seat_id: str):
    agent = agent_repo.assign_seat(agent_id, seat_id)
    if not agent:
        raise HTTPException(404, "Agent not found")
    return agent.to_dict()


@router.post("/agents/{agent_id}/unseat")
async def unseat_agent(agent_id: str):
    agent = agent_repo.unseat(agent_id)
    if not agent:
        raise HTTPException(404, "Agent not found")
    return agent.to_dict()


# ── Seats ────────────────────────────────────────────────────────────────────

@router.get("/seats")
async def list_seats():
    return [s.to_dict() for s in seat_repo.list_all()]


@router.get("/seats/{seat_id}")
async def get_seat(seat_id: str):
    seat = seat_repo.get(seat_id)
    if not seat:
        raise HTTPException(404, "Seat not found")
    return seat.to_dict()


@router.get("/seats/empty")
async def list_empty_seats():
    return [s.to_dict() for s in seat_repo.get_empty()]


# ── Regions ──────────────────────────────────────────────────────────────────

@router.get("/regions")
async def list_regions():
    return [r.to_dict() for r in region_repo.list_all()]


@router.get("/regions/{region_id}")
async def get_region(region_id: str):
    region = region_repo.get(region_id)
    if not region:
        raise HTTPException(404, "Region not found")
    return region.to_dict()


@router.post("/regions")
async def create_region(body: dict):
    from ..models.region import Region, RegionType
    region = Region(
        name=body["name"],
        description=body.get("description"),
        color=body.get("color", "#8b5cf6"),
        region_type=RegionType(body.get("region_type", "manual")),
        arc_start_deg=body.get("arc_start_deg"),
        arc_end_deg=body.get("arc_end_deg"),
    )
    created = region_repo.create(region)

    # Assign seats if provided
    seat_ids = body.get("seat_ids", [])
    if seat_ids:
        seat_repo.assign_region(seat_ids, created.id)
        created = region_repo.get(created.id)

    return created.to_dict()


@router.put("/regions/{region_id}")
async def update_region(region_id: str, body: dict):
    # Handle seat assignment separately
    seat_ids = body.pop("seat_ids", None)
    updated = region_repo.update(region_id, **body)
    if not updated:
        raise HTTPException(404, "Region not found")

    if seat_ids is not None:
        # Clear existing seats from this region
        seat_repo.assign_region(
            [s.id for s in seat_repo.get_by_region(region_id)], None
        )
        # Assign new seats
        seat_repo.assign_region(seat_ids, region_id)
        updated = region_repo.get(region_id)

    return updated.to_dict()


@router.delete("/regions/{region_id}")
async def delete_region(region_id: str):
    if not region_repo.delete(region_id):
        raise HTTPException(404, "Region not found")
    return {"ok": True}


@router.post("/regions/{region_id}/seats")
async def assign_seats_to_region(region_id: str, body: dict):
    """Add seats to a region."""
    seat_ids = body.get("seat_ids", [])
    count = seat_repo.assign_region(seat_ids, region_id)
    return {"assigned": count}


# ── IO Ports ─────────────────────────────────────────────────────────────────

@router.get("/io-ports")
async def list_io_ports(region_id: Optional[str] = None, direction: Optional[str] = None):
    return [p.to_dict() for p in io_port_repo.list_all(region_id, direction)]


@router.get("/io-ports/{port_id}")
async def get_io_port(port_id: str):
    port = io_port_repo.get(port_id)
    if not port:
        raise HTTPException(404, "IO Port not found")
    return port.to_dict()


@router.post("/io-ports")
async def create_io_port(body: dict):
    from ..models.io_port import IOPort, IODirection
    port = IOPort(
        name=body["name"],
        direction=IODirection(body.get("direction", "input")),
        description=body.get("description"),
        region_id=body.get("region_id"),
        data_type=body.get("data_type"),
        schema_json=body.get("schema_json"),
        color=body.get("color", "#10b981"),
    )
    created = io_port_repo.create(port)
    return created.to_dict()


@router.put("/io-ports/{port_id}")
async def update_io_port(port_id: str, body: dict):
    updated = io_port_repo.update(port_id, **body)
    if not updated:
        raise HTTPException(404, "IO Port not found")
    return updated.to_dict()


@router.delete("/io-ports/{port_id}")
async def delete_io_port(port_id: str):
    if not io_port_repo.delete(port_id):
        raise HTTPException(404, "IO Port not found")
    return {"ok": True}


# ── Constitution ─────────────────────────────────────────────────────────────

@router.get("/settings")
async def get_settings():
    """Return connection info, paths, and server metadata."""
    import socket
    from ..config import DATA_DIR, read_port_file
    port = read_port_file() or 8090
    return {
        "version": "0.1.0",
        "host": "127.0.0.1",
        "port": port,
        "api_url": f"http://127.0.0.1:{port}/api",
        "db_path": str(DATA_DIR / "council.db"),
        "data_dir": str(DATA_DIR),
        "mcp_command": "python -m council_mcp.server",
        "mcp_config": {
            "mcpServers": {
                "council": {
                    "command": "python",
                    "args": ["-m", "council_mcp.server"],
                }
            }
        },
    }


@router.get("/constitution")
async def get_constitution():
    """Get the active constitution."""
    active = constitution_repo.get_active()
    if not active:
        return {"id": None, "version": 0, "preamble": "", "rules": "", "goals": "", "constraints": "", "is_active": False, "created_by": None, "created_at": None}
    return active.to_dict()


@router.get("/constitutions")
async def list_constitutions():
    """List all constitution versions (audit trail)."""
    return [c.to_dict() for c in constitution_repo.list_all()]


@router.post("/constitutions")
async def create_constitution(body: dict):
    """Create a new constitution version and set it as active."""
    created = constitution_repo.create(
        preamble=body.get("preamble", ""),
        rules=body.get("rules", ""),
        goals=body.get("goals", ""),
        constraints=body.get("constraints", ""),
        created_by=body.get("created_by"),
        activate=body.get("activate", True),
    )
    return created.to_dict()


@router.put("/constitution")
async def update_constitution(body: dict):
    """Convenience: create a new version and activate it (backward compat)."""
    created = constitution_repo.create(
        preamble=body.get("preamble", ""),
        rules=body.get("rules", ""),
        goals=body.get("goals", ""),
        constraints=body.get("constraints", ""),
        created_by=body.get("created_by"),
        activate=True,
    )
    return created.to_dict()


@router.post("/constitutions/{constitution_id}/activate")
async def activate_constitution(constitution_id: str):
    """Activate a specific constitution version."""
    activated = constitution_repo.activate(constitution_id)
    if not activated:
        raise HTTPException(404, "Constitution not found")
    return activated.to_dict()


# ── Discussions ──────────────────────────────────────────────────────────────

@router.get("/discussions")
async def list_discussions(limit: int = 50):
    return [d.to_dict() for d in discussion_repo.list_all(limit)]


@router.get("/discussions/{discussion_id}")
async def get_discussion(discussion_id: str):
    d = discussion_repo.get(discussion_id)
    if not d:
        raise HTTPException(404, "Discussion not found")
    return d.to_dict()


@router.post("/discussions")
async def create_discussion(body: dict):
    """Create a new discussion topic."""
    d = discussion_repo.create(
        topic=body["topic"],
        description=body.get("description"),
        created_by=body.get("created_by"),
    )
    return d.to_dict()


@router.post("/discussions/{discussion_id}/deliberate")
async def deliberate_discussion(discussion_id: str, body: dict = None):
    """Run a round of deliberation: all seated agents respond to the topic.

    Optional body:
      agent_ids: list of specific agent IDs to include (default: all seated)
      rounds: number of deliberation rounds (default: 1)
      api_key: optional API key to use for this deliberation
      provider: optional provider override (anthropic, openai)
    """
    import os
    from ..services.deliberation import deliberate

    body = body or {}
    d = discussion_repo.get(discussion_id)
    if not d:
        raise HTTPException(404, "Discussion not found")

    # Allow per-request API key injection
    api_key = body.get("api_key")
    provider = body.get("provider", "anthropic")
    if api_key:
        if provider == "anthropic":
            os.environ["ANTHROPIC_API_KEY"] = api_key
        elif provider == "openai":
            os.environ["OPENAI_API_KEY"] = api_key

    # Update status
    discussion_repo.update_status(discussion_id, "deliberating")

    # Get agents to participate
    all_agents = agent_repo.list_all()
    seated_agents = [a for a in all_agents if a.seat_id]

    agent_ids = body.get("agent_ids")
    if agent_ids:
        seated_agents = [a for a in seated_agents if a.id in agent_ids]

    if not seated_agents:
        raise HTTPException(400, "No seated agents available for deliberation")

    # Build region name lookup
    regions = region_repo.list_all()
    seats = seat_repo.list_all()
    seat_region = {}
    for s in seats:
        if s.agent_id and s.region_id:
            region = next((r for r in regions if r.id == s.region_id), None)
            if region:
                seat_region[s.agent_id] = region.name

    # Get constitution
    constitution = constitution_repo.get_active()

    # Run deliberation rounds
    rounds = body.get("rounds", 1)
    all_new_messages = []

    for round_num in range(rounds):
        # Gather prior messages for context
        prior = [m.to_dict() for m in d.messages] + [m for m in all_new_messages]

        results = await deliberate(
            topic=d.topic,
            agents=seated_agents,
            constitution=constitution,
            region_names=seat_region,
            prior_messages=prior if prior else None,
        )

        # Record messages
        for r in results:
            msg = discussion_repo.add_message(
                discussion_id=discussion_id,
                agent_id=r["agent_id"],
                agent_name=r["agent_name"],
                content=r.get("content", "[awaiting delegation]"),
                agent_role=r["agent_role"],
                message_type="statement",
            )
            all_new_messages.append(msg.to_dict())

    # Reload discussion with all messages
    d = discussion_repo.get(discussion_id)
    return d.to_dict()


@router.post("/discussions/{discussion_id}/conclude")
async def conclude_discussion(discussion_id: str, body: dict = None):
    """Mark a discussion as concluded with an optional summary."""
    body = body or {}
    d = discussion_repo.update_status(
        discussion_id, "concluded",
        conclusion=body.get("conclusion"),
    )
    if not d:
        raise HTTPException(404, "Discussion not found")
    return d.to_dict()


@router.post("/discussions/{discussion_id}/message")
async def add_manual_message(discussion_id: str, body: dict):
    """Add a manual message to a discussion (e.g. from a human moderator)."""
    d = discussion_repo.get(discussion_id)
    if not d:
        raise HTTPException(404, "Discussion not found")
    msg = discussion_repo.add_message(
        discussion_id=discussion_id,
        agent_id=body.get("agent_id", "human"),
        agent_name=body.get("agent_name", "Moderator"),
        content=body["content"],
        agent_role=body.get("agent_role", "moderator"),
        message_type=body.get("message_type", "statement"),
    )
    return msg.to_dict()


# ── Tool Connection (MCP injection) ──────────────────────────────────────────

def _get_mcp_command() -> tuple:
    """
    Determine the best command + args to run Council as an MCP stdio server.
    Returns (command, args, needs_pip_install, env)
    """
    import shutil
    import sys
    from pathlib import Path

    # Find the council project root (parent of the council/ package)
    council_root = str(Path(__file__).parent.parent.parent)

    # Prefer the Python that's currently running this backend
    python_bin = sys.executable

    # Fallback to system Python
    if not python_bin or not Path(python_bin).exists():
        for candidate in [
            shutil.which("python3"),
            shutil.which("python"),
            "/opt/homebrew/bin/python3",
            "/usr/local/bin/python3",
            "/usr/bin/python3",
        ]:
            if candidate and Path(candidate).exists():
                python_bin = candidate
                break

    if python_bin:
        return (python_bin, ["-m", "council_mcp.server"], False, {"PYTHONPATH": council_root})

    return (None, [], False, {})


def _connect_goose(cmd: str, args: list, council_db: str, env: dict = None) -> dict:
    """Add Council extension to Goose config.yaml."""
    import yaml
    from pathlib import Path

    config_path = Path.home() / ".config" / "goose" / "config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)

    cfg = {}
    if config_path.exists():
        with open(config_path) as f:
            cfg = yaml.safe_load(f) or {}

    if "extensions" not in cfg:
        cfg["extensions"] = {}

    envs = {"COUNCIL_DB": council_db}
    if env:
        envs.update(env)

    cfg["extensions"]["council"] = {
        "enabled": True,
        "type": "stdio",
        "name": "Council",
        "description": "Agent governance parliament — manage agents, regions, discussions",
        "cmd": cmd,
        "args": args,
        "envs": envs,
        "env_keys": [],
        "timeout": 300,
    }

    with open(config_path, "w") as f:
        yaml.dump(cfg, f, default_flow_style=False, sort_keys=False)

    return {"tool": "goose", "status": "connected", "config_path": str(config_path)}


def _connect_claude(cmd: str, args: list, council_db: str, env: dict = None) -> dict:
    """Add Council MCP server to Claude Desktop config."""
    import json as _json
    from pathlib import Path

    config_path = Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)

    cfg = {}
    if config_path.exists():
        with open(config_path) as f:
            cfg = _json.load(f)

    if "mcpServers" not in cfg:
        cfg["mcpServers"] = {}

    mcp_env = {"COUNCIL_DB": council_db}
    if env:
        mcp_env.update(env)

    cfg["mcpServers"]["council"] = {
        "command": cmd,
        "args": args,
        "env": mcp_env,
    }

    with open(config_path, "w") as f:
        _json.dump(cfg, f, indent=2)

    return {"tool": "claude", "status": "connected", "config_path": str(config_path)}


def _connect_cursor(cmd: str, args: list, council_db: str, env: dict = None) -> dict:
    """Add Council MCP server to Cursor config."""
    import json as _json
    from pathlib import Path

    config_path = Path.home() / ".cursor" / "mcp.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)

    cfg = {}
    if config_path.exists():
        with open(config_path) as f:
            cfg = _json.load(f)

    if "mcpServers" not in cfg:
        cfg["mcpServers"] = {}

    mcp_env = {"COUNCIL_DB": council_db}
    if env:
        mcp_env.update(env)

    cfg["mcpServers"]["council"] = {
        "command": cmd,
        "args": args,
        "env": mcp_env,
    }

    with open(config_path, "w") as f:
        _json.dump(cfg, f, indent=2)

    return {"tool": "cursor", "status": "connected", "config_path": str(config_path)}


def _connect_windsurf(cmd: str, args: list, council_db: str, env: dict = None) -> dict:
    """Add Council MCP server to Windsurf/Codeium config."""
    import json as _json
    from pathlib import Path

    config_path = Path.home() / ".codeium" / "windsurf" / "mcp_config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)

    cfg = {}
    if config_path.exists():
        with open(config_path) as f:
            cfg = _json.load(f)

    if "mcpServers" not in cfg:
        cfg["mcpServers"] = {}

    mcp_env = {"COUNCIL_DB": council_db}
    if env:
        mcp_env.update(env)

    cfg["mcpServers"]["council"] = {
        "command": cmd,
        "args": args,
        "env": mcp_env,
    }

    with open(config_path, "w") as f:
        _json.dump(cfg, f, indent=2)

    return {"tool": "windsurf", "status": "connected", "config_path": str(config_path)}


@router.get("/tools/status")
async def get_tool_status():
    """Check which AI tools have Council configured."""
    import json as _json
    from pathlib import Path

    status = {}

    # Goose
    goose_config = Path.home() / ".config" / "goose" / "config.yaml"
    try:
        if goose_config.exists():
            import yaml
            with open(goose_config) as f:
                cfg = yaml.safe_load(f)
            exts = cfg.get("extensions", {})
            status["goose"] = "council" in exts and exts["council"].get("enabled", False)
        else:
            status["goose"] = False
    except Exception:
        status["goose"] = False

    # Claude Desktop
    claude_config = Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    try:
        if claude_config.exists():
            with open(claude_config) as f:
                cfg = _json.load(f)
            status["claude"] = "council" in cfg.get("mcpServers", {})
        else:
            status["claude"] = False
    except Exception:
        status["claude"] = False

    # Cursor
    cursor_config = Path.home() / ".cursor" / "mcp.json"
    try:
        if cursor_config.exists():
            with open(cursor_config) as f:
                cfg = _json.load(f)
            status["cursor"] = "council" in cfg.get("mcpServers", {})
        else:
            status["cursor"] = False
    except Exception:
        status["cursor"] = False

    # Windsurf
    windsurf_config = Path.home() / ".codeium" / "windsurf" / "mcp_config.json"
    try:
        if windsurf_config.exists():
            with open(windsurf_config) as f:
                cfg = _json.load(f)
            status["windsurf"] = "council" in cfg.get("mcpServers", {})
        else:
            status["windsurf"] = False
    except Exception:
        status["windsurf"] = False

    return status


@router.post("/tools/connect")
async def connect_tool(data: dict):
    """Connect Council as an MCP server to a specific AI tool."""
    from pathlib import Path

    tool = data.get("tool")
    if not tool:
        raise HTTPException(status_code=400, detail="Missing 'tool' field")

    council_db = str(Path.home() / ".council" / "council.db")
    cmd, args, _, env = _get_mcp_command()
    if not cmd:
        raise HTTPException(status_code=500, detail="Could not find Python interpreter")

    connectors = {
        "goose": _connect_goose,
        "claude": _connect_claude,
        "cursor": _connect_cursor,
        "windsurf": _connect_windsurf,
    }

    connector = connectors.get(tool)
    if not connector:
        raise HTTPException(status_code=400, detail=f"Unknown tool: {tool}")

    return connector(cmd, args, council_db, env)


@router.post("/tools/auto-connect")
async def auto_connect_tools():
    """
    Automatically configure Council MCP for all detected AI tools.
    Called during onboarding — writes config for every tool whose config dir exists.
    """
    from pathlib import Path

    council_db = str(Path.home() / ".council" / "council.db")
    cmd, args, _, env = _get_mcp_command()
    if not cmd:
        raise HTTPException(status_code=500, detail="Could not find Python interpreter")

    results = {}

    # Goose — always configure
    try:
        results["goose"] = _connect_goose(cmd, args, council_db, env)
    except Exception as e:
        results["goose"] = {"status": "error", "detail": str(e)}

    # Claude Desktop
    claude_dir = Path.home() / "Library" / "Application Support" / "Claude"
    if claude_dir.exists():
        try:
            results["claude"] = _connect_claude(cmd, args, council_db, env)
        except Exception as e:
            results["claude"] = {"status": "error", "detail": str(e)}
    else:
        results["claude"] = {"status": "skipped", "detail": "Claude Desktop not installed"}

    # Cursor
    cursor_dir = Path.home() / ".cursor"
    if cursor_dir.exists():
        try:
            results["cursor"] = _connect_cursor(cmd, args, council_db, env)
        except Exception as e:
            results["cursor"] = {"status": "error", "detail": str(e)}
    else:
        results["cursor"] = {"status": "skipped", "detail": "Cursor not installed"}

    # Windsurf
    windsurf_dir = Path.home() / ".codeium" / "windsurf"
    if windsurf_dir.exists():
        try:
            results["windsurf"] = _connect_windsurf(cmd, args, council_db, env)
        except Exception as e:
            results["windsurf"] = {"status": "error", "detail": str(e)}
    else:
        results["windsurf"] = {"status": "skipped", "detail": "Windsurf not installed"}

    return {
        "auto_connect": True,
        "mcp_command": cmd,
        "mcp_args": args,
        "results": results,
    }


@router.get("/tools/mcp-info")
async def get_mcp_info():
    """Return MCP server command info for manual configuration."""
    from pathlib import Path

    cmd, args, _, mcp_env = _get_mcp_command()
    council_db = str(Path.home() / ".council" / "council.db")

    env = {"COUNCIL_DB": council_db}
    if mcp_env:
        env.update(mcp_env)

    return {
        "command": cmd,
        "args": args,
        "env": env,
    }
