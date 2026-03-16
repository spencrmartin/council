#!/usr/bin/env python3
"""
Council MCP Server

Exposes Council's agent governance capabilities through the Model Context Protocol.
Allows AI assistants to manage agents, seats, regions, and I/O ports.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path to import council modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from council.database.connection import Database
from council.database.repository import (
    AgentRepository,
    SeatRepository,
    RegionRepository,
    IOPortRepository,
    ConstitutionRepository,
    DiscussionRepository,
)
from council.database.community_repository import (
    CommunityMemberRepository,
    FocusGroupRepository,
    CommunityPollRepository,
)
from council.models.agent import Agent, AgentRole, AgentStatus
from council.models.seat import Seat
from council.models.region import Region, RegionType
from council.models.io_port import IOPort, IODirection

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ReadResourceRequest,
    ServerResult,
    TextResourceContents,
)

# Initialize server
server = Server("council-governance")

# Global repository instances
agent_repo: Optional[AgentRepository] = None
seat_repo: Optional[SeatRepository] = None
region_repo: Optional[RegionRepository] = None
io_port_repo: Optional[IOPortRepository] = None
constitution_repo: Optional[ConstitutionRepository] = None
discussion_repo: Optional[DiscussionRepository] = None
community_member_repo: Optional[CommunityMemberRepository] = None
focus_group_repo: Optional[FocusGroupRepository] = None
community_poll_repo: Optional[CommunityPollRepository] = None


def init_services():
    """Initialize database connection and repositories"""
    global agent_repo, seat_repo, region_repo, io_port_repo, constitution_repo, discussion_repo
    global community_member_repo, focus_group_repo, community_poll_repo
    db_path = os.path.expanduser("~/.council/council.db")
    db = Database(db_path)
    agent_repo = AgentRepository(db)
    seat_repo = SeatRepository(db)
    region_repo = RegionRepository(db)
    io_port_repo = IOPortRepository(db)
    constitution_repo = ConstitutionRepository(db)
    discussion_repo = DiscussionRepository(db)
    community_member_repo = CommunityMemberRepository(db)
    focus_group_repo = FocusGroupRepository(db)
    community_poll_repo = CommunityPollRepository(db)


# ── Resources ────────────────────────────────────────────────────────────────

@server.list_resources()
async def handle_list_resources() -> list[Resource]:
    return [
        Resource(
            uri="council://overview",
            name="Council Overview",
            description="Full state of the council: agents, seats, regions, I/O ports",
            mimeType="application/json",
        ),
        Resource(
            uri="council://stats",
            name="Council Statistics",
            description="Summary statistics about the council",
            mimeType="application/json",
        ),
    ]


@server.read_resource()
async def handle_read_resource(req: ReadResourceRequest) -> ServerResult:
    uri = str(req.params.uri)

    if uri == "council://overview":
        seats = [s.to_dict() for s in seat_repo.list_all()]
        agents = [a.to_dict() for a in agent_repo.list_all()]
        regions = [r.to_dict() for r in region_repo.list_all()]
        io_ports = [p.to_dict() for p in io_port_repo.list_all()]
        data = {
            "seats": seats,
            "agents": agents,
            "regions": regions,
            "io_ports": io_ports,
        }
        return ServerResult(
            contents=[TextResourceContents(uri=uri, text=json.dumps(data, indent=2), mimeType="application/json")]
        )

    if uri == "council://stats":
        seats = seat_repo.list_all()
        agents = agent_repo.list_all()
        regions = region_repo.list_all()
        io_ports = io_port_repo.list_all()
        stats = {
            "total_seats": len(seats),
            "occupied_seats": sum(1 for s in seats if s.agent_id),
            "empty_seats": sum(1 for s in seats if not s.agent_id),
            "total_agents": len(agents),
            "seated_agents": sum(1 for a in agents if a.seat_id),
            "unseated_agents": sum(1 for a in agents if not a.seat_id),
            "total_regions": len(regions),
            "total_inputs": sum(1 for p in io_ports if p.direction == IODirection.INPUT),
            "total_outputs": sum(1 for p in io_ports if p.direction == IODirection.OUTPUT),
        }
        return ServerResult(
            contents=[TextResourceContents(uri=uri, text=json.dumps(stats, indent=2), mimeType="application/json")]
        )

    raise ValueError(f"Unknown resource: {uri}")


# ── Tools ────────────────────────────────────────────────────────────────────

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return [
        # ── Agent tools ──
        Tool(
            name="council_list_agents",
            description="List all agents in the council",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="council_create_agent",
            description="Create a new agent. Roles: speaker, minister, delegate, observer, auditor.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Agent name"},
                    "role": {"type": "string", "enum": ["speaker", "minister", "delegate", "observer", "auditor"], "default": "delegate"},
                    "description": {"type": "string", "description": "What this agent does"},
                    "icon": {"type": "string", "description": "Lucide icon name (e.g. bot, brain, shield, eye, search, target, zap, lock, bar-chart, palette)", "default": "bot"},
                    "model_provider": {"type": "string", "description": "e.g. anthropic, openai"},
                    "model_name": {"type": "string", "description": "e.g. claude-sonnet-4, gpt-4o"},
                    "color": {"type": "string", "description": "Hex color for seat highlight"},
                },
                "required": ["name"],
            },
        ),
        Tool(
            name="council_assign_seat",
            description="Assign an agent to a specific seat in the council",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_id": {"type": "string"},
                    "seat_id": {"type": "string"},
                },
                "required": ["agent_id", "seat_id"],
            },
        ),
        Tool(
            name="council_unseat_agent",
            description="Remove an agent from their seat",
            inputSchema={
                "type": "object",
                "properties": {"agent_id": {"type": "string"}},
                "required": ["agent_id"],
            },
        ),
        Tool(
            name="council_delete_agent",
            description="Delete an agent from the council",
            inputSchema={
                "type": "object",
                "properties": {"agent_id": {"type": "string"}},
                "required": ["agent_id"],
            },
        ),

        # ── Seat tools ──
        Tool(
            name="council_list_seats",
            description="List all seats in the council hemicycle",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="council_list_empty_seats",
            description="List all unoccupied seats",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),

        # ── Region tools ──
        Tool(
            name="council_list_regions",
            description="List all regions with their seats and I/O ports",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="council_create_region",
            description="Create a new region to group seats and assign I/O responsibilities",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Region name"},
                    "description": {"type": "string"},
                    "color": {"type": "string", "description": "Hex color"},
                    "seat_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Seat IDs to include in this region",
                    },
                },
                "required": ["name"],
            },
        ),
        Tool(
            name="council_delete_region",
            description="Delete a region (seats are unassigned, not deleted)",
            inputSchema={
                "type": "object",
                "properties": {"region_id": {"type": "string"}},
                "required": ["region_id"],
            },
        ),
        Tool(
            name="council_assign_seats_to_region",
            description="Assign a list of seats to a region",
            inputSchema={
                "type": "object",
                "properties": {
                    "region_id": {"type": "string"},
                    "seat_ids": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["region_id", "seat_ids"],
            },
        ),

        # ── IO Port tools ──
        Tool(
            name="council_list_io_ports",
            description="List all I/O ports, optionally filtered by region or direction",
            inputSchema={
                "type": "object",
                "properties": {
                    "region_id": {"type": "string"},
                    "direction": {"type": "string", "enum": ["input", "output"]},
                },
                "required": [],
            },
        ),
        Tool(
            name="council_create_io_port",
            description="Create an input or output port and optionally assign it to a region",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Port name"},
                    "direction": {"type": "string", "enum": ["input", "output"]},
                    "description": {"type": "string"},
                    "region_id": {"type": "string", "description": "Region to assign to"},
                    "data_type": {"type": "string", "description": "e.g. text, json, image, event"},
                },
                "required": ["name", "direction"],
            },
        ),
        Tool(
            name="council_delete_io_port",
            description="Delete an I/O port",
            inputSchema={
                "type": "object",
                "properties": {"port_id": {"type": "string"}},
                "required": ["port_id"],
            },
        ),

        # ── Overview ──
        Tool(
            name="council_overview",
            description="Get full council state: all agents, seats, regions, I/O ports, and statistics",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),

        # ── Discussion tools ──
        Tool(
            name="council_start_discussion",
            description="Start a new discussion topic in the council. Returns the discussion object.",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "The topic or question to discuss"},
                    "description": {"type": "string", "description": "Additional context"},
                },
                "required": ["topic"],
            },
        ),
        Tool(
            name="council_deliberate",
            description="Have all seated agents deliberate on a discussion topic. Each agent responds based on their role, region, and the active constitution. Can run multiple rounds.",
            inputSchema={
                "type": "object",
                "properties": {
                    "discussion_id": {"type": "string", "description": "ID of the discussion to deliberate on"},
                    "rounds": {"type": "integer", "description": "Number of deliberation rounds (default: 1)", "default": 1},
                    "agent_ids": {"type": "array", "items": {"type": "string"}, "description": "Specific agent IDs to include (default: all seated agents)"},
                },
                "required": ["discussion_id"],
            },
        ),
        Tool(
            name="council_discuss",
            description="Shortcut: create a discussion AND run deliberation in one call. Returns the full discussion with all agent responses.",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "The topic or question for the council to discuss"},
                    "rounds": {"type": "integer", "description": "Number of deliberation rounds (default: 1)", "default": 1},
                },
                "required": ["topic"],
            },
        ),
        Tool(
            name="council_conclude_discussion",
            description="Mark a discussion as concluded with a summary/decision.",
            inputSchema={
                "type": "object",
                "properties": {
                    "discussion_id": {"type": "string"},
                    "conclusion": {"type": "string", "description": "The final decision or summary"},
                },
                "required": ["discussion_id"],
            },
        ),
        Tool(
            name="council_list_discussions",
            description="List all council discussions (recent first).",
            inputSchema={"type": "object", "properties": {"limit": {"type": "integer", "default": 20}}, "required": []},
        ),
        Tool(
            name="council_get_discussion",
            description="Get a specific discussion with all messages.",
            inputSchema={
                "type": "object",
                "properties": {"discussion_id": {"type": "string"}},
                "required": ["discussion_id"],
            },
        ),

        # ── Briefing / Task tools ──
        Tool(
            name="council_briefing",
            description="Get a briefing package for all seated agents. Returns each agent's name, role, region, and a system prompt built from the active constitution. Use this to delegate tasks to agents — pass each agent's system_prompt as instructions to a subagent.",
            inputSchema={
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "The task or question to brief agents on"},
                    "agent_ids": {"type": "array", "items": {"type": "string"}, "description": "Specific agent IDs (default: all seated)"},
                },
                "required": ["task"],
            },
        ),
        Tool(
            name="council_send",
            description="Send a task to the entire council. Creates a discussion, runs deliberation (each agent responds via their configured model), and returns all responses. This is the main way to get the council's input on something. Set ANTHROPIC_API_KEY or OPENAI_API_KEY env vars for the agents' model providers. If no provider is configured or available, returns delegation packages — use the delegate tool to spin up subagents with each agent's system_prompt as instructions, then record their responses.",
            inputSchema={
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "The task, question, or topic to send to the council"},
                    "rounds": {"type": "integer", "description": "Deliberation rounds — in round 2+, agents see prior responses (default: 1)", "default": 1},
                },
                "required": ["task"],
            },
        ),

        # ── Constitution tools ──
        Tool(
            name="council_get_constitution",
            description="Get the active constitution — the governing rules, goals, and constraints for the council.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="council_create_constitution",
            description="Create a new constitution version and set it as active. Previous versions are kept for audit.",
            inputSchema={
                "type": "object",
                "properties": {
                    "preamble": {"type": "string", "description": "High-level purpose statement"},
                    "rules": {"type": "string", "description": "Operating rules (markdown)"},
                    "goals": {"type": "string", "description": "Objectives (markdown)"},
                    "constraints": {"type": "string", "description": "Boundaries and limitations (markdown)"},
                },
                "required": [],
            },
        ),
        Tool(
            name="council_list_constitutions",
            description="List all constitution versions (audit trail), newest first.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),

        # ── Community tools ──
        Tool(
            name="council_list_members",
            description="List all 60 community members. These are diverse personas across 6 cohorts (builders, operators, advocates, pragmatists, creatives, skeptics) that can be engaged through focus groups, polls, and consultations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "cohort": {"type": "string", "enum": ["builders", "operators", "advocates", "pragmatists", "creatives", "skeptics"], "description": "Filter by cohort"},
                    "active_only": {"type": "boolean", "default": True},
                },
                "required": [],
            },
        ),
        Tool(
            name="council_get_member",
            description="Get full profile of a specific community member — their background, passions, values, and communication style.",
            inputSchema={
                "type": "object",
                "properties": {"member_id": {"type": "string"}},
                "required": ["member_id"],
            },
        ),
        Tool(
            name="council_create_member",
            description="Create a custom community member with unique perspective and voice.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Member name"},
                    "cohort": {"type": "string", "enum": ["builders", "operators", "advocates", "pragmatists", "creatives", "skeptics"]},
                    "age": {"type": "integer"},
                    "profession": {"type": "string"},
                    "background": {"type": "string", "description": "Short bio"},
                    "passions": {"type": "array", "items": {"type": "string"}},
                    "core_values": {"type": "array", "items": {"type": "string"}},
                    "communication_style": {"type": "string"},
                    "perspective_summary": {"type": "string", "description": "2-3 sentence worldview"},
                },
                "required": ["name", "cohort"],
            },
        ),
        Tool(
            name="council_update_member",
            description="Update an existing community member's profile.",
            inputSchema={
                "type": "object",
                "properties": {
                    "member_id": {"type": "string"},
                    "name": {"type": "string"},
                    "cohort": {"type": "string", "enum": ["builders", "operators", "advocates", "pragmatists", "creatives", "skeptics"]},
                    "age": {"type": "integer"},
                    "profession": {"type": "string"},
                    "background": {"type": "string"},
                    "passions": {"type": "array", "items": {"type": "string"}},
                    "core_values": {"type": "array", "items": {"type": "string"}},
                    "communication_style": {"type": "string"},
                    "perspective_summary": {"type": "string"},
                    "is_active": {"type": "boolean"},
                },
                "required": ["member_id"],
            },
        ),
        Tool(
            name="council_delete_member",
            description="Delete a community member.",
            inputSchema={
                "type": "object",
                "properties": {"member_id": {"type": "string"}},
                "required": ["member_id"],
            },
        ),
        Tool(
            name="council_focus_group",
            description="Convene a focus group of community members to discuss a topic. Members are selected by method: 'diverse' (one from each cohort), 'random', 'cohort' (all from one cohort), or 'targeted' (by passion/interest). Returns each member's perspective, sentiment, and a synthesis. Can be called mid-deliberation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "The topic for the focus group to discuss"},
                    "method": {"type": "string", "enum": ["random", "cohort", "diverse", "targeted"], "default": "diverse", "description": "How to select members"},
                    "size": {"type": "integer", "default": 8, "description": "Number of members (default: 8)"},
                    "cohort_filter": {"type": "string", "description": "Cohort name (for method='cohort')"},
                    "passion_filter": {"type": "string", "description": "Passion/interest keyword (for method='targeted')"},
                    "discussion_id": {"type": "string", "description": "Optional council discussion ID to link to"},
                },
                "required": ["topic"],
            },
        ),
        Tool(
            name="council_poll",
            description="Run a quick sentiment poll across all 60 community members (or a subset). Returns support/oppose/neutral percentages, top concerns, and top endorsements.",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "The poll question"},
                    "method": {"type": "string", "enum": ["all", "random", "cohort", "diverse", "targeted"], "default": "all"},
                    "size": {"type": "integer", "description": "Number of members to poll (default: all)"},
                    "cohort_filter": {"type": "string"},
                    "passion_filter": {"type": "string"},
                    "discussion_id": {"type": "string"},
                },
                "required": ["question"],
            },
        ),
        Tool(
            name="council_town_hall",
            description="Run a town hall where community members react to a council proposal. More free-form than a focus group — members can support, oppose, question, or propose amendments. Returns reactions, overall sentiment, and key themes.",
            inputSchema={
                "type": "object",
                "properties": {
                    "proposal": {"type": "string", "description": "The council proposal for community reaction"},
                    "size": {"type": "integer", "default": 20, "description": "Number of members to include (default: 20)"},
                },
                "required": ["proposal"],
            },
        ),
        Tool(
            name="council_consult_member",
            description="Have a deep-dive one-on-one consultation with a specific community member. The member responds in character with their unique voice and perspective.",
            inputSchema={
                "type": "object",
                "properties": {
                    "member_id": {"type": "string", "description": "ID of the member to consult"},
                    "question": {"type": "string", "description": "The question or topic to discuss"},
                },
                "required": ["member_id", "question"],
            },
        ),
        Tool(
            name="council_community_stats",
            description="Get community statistics — member counts by cohort, custom vs default members.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        result = await _dispatch_tool(name, arguments)
        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def _dispatch_tool(name: str, args: dict):
    # ── Agents ──
    if name == "council_list_agents":
        return [a.to_dict() for a in agent_repo.list_all()]

    if name == "council_create_agent":
        agent = Agent(
            name=args["name"],
            role=AgentRole(args.get("role", "delegate")),
            description=args.get("description"),
            model_provider=args.get("model_provider"),
            model_name=args.get("model_name"),
            icon=args.get("icon", "bot"),
            color=args.get("color", "#6366f1"),
        )
        created = agent_repo.create(agent)
        return created.to_dict()

    if name == "council_assign_seat":
        agent = agent_repo.assign_seat(args["agent_id"], args["seat_id"])
        if not agent:
            raise ValueError("Agent not found")
        return agent.to_dict()

    if name == "council_unseat_agent":
        agent = agent_repo.unseat(args["agent_id"])
        if not agent:
            raise ValueError("Agent not found")
        return agent.to_dict()

    if name == "council_delete_agent":
        if not agent_repo.delete(args["agent_id"]):
            raise ValueError("Agent not found")
        return {"ok": True}

    # ── Seats ──
    if name == "council_list_seats":
        return [s.to_dict() for s in seat_repo.list_all()]

    if name == "council_list_empty_seats":
        return [s.to_dict() for s in seat_repo.get_empty()]

    # ── Regions ──
    if name == "council_list_regions":
        return [r.to_dict() for r in region_repo.list_all()]

    if name == "council_create_region":
        region = Region(
            name=args["name"],
            description=args.get("description"),
            color=args.get("color", "#8b5cf6"),
        )
        created = region_repo.create(region)
        seat_ids = args.get("seat_ids", [])
        if seat_ids:
            seat_repo.assign_region(seat_ids, created.id)
            created = region_repo.get(created.id)
        return created.to_dict()

    if name == "council_delete_region":
        if not region_repo.delete(args["region_id"]):
            raise ValueError("Region not found")
        return {"ok": True}

    if name == "council_assign_seats_to_region":
        count = seat_repo.assign_region(args["seat_ids"], args["region_id"])
        return {"assigned": count}

    # ── IO Ports ──
    if name == "council_list_io_ports":
        return [p.to_dict() for p in io_port_repo.list_all(
            region_id=args.get("region_id"),
            direction=args.get("direction"),
        )]

    if name == "council_create_io_port":
        port = IOPort(
            name=args["name"],
            direction=IODirection(args["direction"]),
            description=args.get("description"),
            region_id=args.get("region_id"),
            data_type=args.get("data_type"),
        )
        created = io_port_repo.create(port)
        return created.to_dict()

    if name == "council_delete_io_port":
        if not io_port_repo.delete(args["port_id"]):
            raise ValueError("IO Port not found")
        return {"ok": True}

    # ── Overview ──
    if name == "council_overview":
        seats = seat_repo.list_all()
        agents = agent_repo.list_all()
        regions = region_repo.list_all()
        io_ports = io_port_repo.list_all()
        constitution = constitution_repo.get_active()
        community_stats = community_member_repo.get_stats()
        agent_map = {a.seat_id: a.to_dict() for a in agents if a.seat_id}
        seat_dicts = []
        for s in seats:
            d = s.to_dict()
            d["agent"] = agent_map.get(s.id)
            seat_dicts.append(d)
        return {
            "seats": seat_dicts,
            "agents": [a.to_dict() for a in agents],
            "regions": [r.to_dict() for r in regions],
            "io_ports": [p.to_dict() for p in io_ports],
            "constitution": constitution.to_dict() if constitution else None,
            "community": community_stats,
            "stats": {
                "total_seats": len(seats),
                "occupied_seats": sum(1 for s in seats if s.agent_id),
                "total_agents": len(agents),
                "total_regions": len(regions),
                "total_inputs": sum(1 for p in io_ports if p.direction == IODirection.INPUT),
                "total_outputs": sum(1 for p in io_ports if p.direction == IODirection.OUTPUT),
                "community_members": community_stats.get("active_members", 0),
            },
        }

    # ── Discussions ──
    if name == "council_list_discussions":
        limit = args.get("limit", 20)
        return [d.to_dict() for d in discussion_repo.list_all(limit)]

    if name == "council_get_discussion":
        d = discussion_repo.get(args["discussion_id"])
        if not d:
            raise ValueError("Discussion not found")
        return d.to_dict()

    if name == "council_start_discussion":
        d = discussion_repo.create(
            topic=args["topic"],
            description=args.get("description"),
        )
        return d.to_dict()

    if name == "council_deliberate":
        from council.services.deliberation import deliberate, check_delegation_needed, build_delegation_packages

        d = discussion_repo.get(args["discussion_id"])
        if not d:
            raise ValueError("Discussion not found")

        all_agents = agent_repo.list_all()
        seated = [a for a in all_agents if a.seat_id]
        agent_ids = args.get("agent_ids")
        if agent_ids:
            seated = [a for a in seated if a.id in agent_ids]
        if not seated:
            raise ValueError("No seated agents available")

        # Region lookup
        regions = region_repo.list_all()
        seats = seat_repo.list_all()
        region_names = {}
        for s in seats:
            if s.agent_id and s.region_id:
                r = next((rg for rg in regions if rg.id == s.region_id), None)
                if r:
                    region_names[s.agent_id] = r.name

        constitution = constitution_repo.get_active()
        rounds = args.get("rounds", 1)

        # Check delegation needs
        needs_delegation = check_delegation_needed(seated)

        if needs_delegation:
            discussion_repo.update_status(d.id, "awaiting_delegation")
            prior = [m.to_dict() for m in d.messages] if d.messages else None
            packages = build_delegation_packages(
                topic=d.topic, agents=seated, constitution=constitution,
                region_names=region_names, prior_messages=prior,
            )
            need_delegate = [p for p in packages if p["needs_delegation"]]

            return {
                "mode": "delegation",
                "discussion_id": d.id,
                "topic": d.topic,
                "message": f"{len(need_delegate)} agent(s) need delegation. Use the delegate tool with each agent's system_prompt as instructions.",
                "delegation_packages": need_delegate,
                "usage_hint": (
                    "For each delegation package, call the delegate tool like this:\n"
                    "  delegate(instructions=package['system_prompt'] + '\\n\\n' + package['user_message'])\n"
                    "Then use council_conclude_discussion to record the final synthesis."
                ),
            }

        # All agents have providers — run directly
        discussion_repo.update_status(d.id, "deliberating")
        all_new = []
        for _ in range(rounds):
            prior = [m.to_dict() for m in d.messages] + all_new
            results = await deliberate(
                topic=d.topic, agents=seated, constitution=constitution,
                region_names=region_names, prior_messages=prior if prior else None,
            )
            for r in results:
                msg = discussion_repo.add_message(
                    discussion_id=d.id, agent_id=r["agent_id"],
                    agent_name=r["agent_name"], content=r["content"],
                    agent_role=r["agent_role"],
                )
                all_new.append(msg.to_dict())

        return discussion_repo.get(d.id).to_dict()

    if name == "council_discuss":
        from council.services.deliberation import deliberate, check_delegation_needed, build_delegation_packages

        # Create + deliberate in one shot
        d = discussion_repo.create(topic=args["topic"])

        all_agents = agent_repo.list_all()
        seated = [a for a in all_agents if a.seat_id]
        if not seated:
            raise ValueError("No seated agents available")

        regions = region_repo.list_all()
        seats = seat_repo.list_all()
        region_names = {}
        for s in seats:
            if s.agent_id and s.region_id:
                r = next((rg for rg in regions if rg.id == s.region_id), None)
                if r:
                    region_names[s.agent_id] = r.name

        constitution = constitution_repo.get_active()
        rounds = args.get("rounds", 1)

        # Check delegation needs
        needs_delegation = check_delegation_needed(seated)

        if needs_delegation:
            discussion_repo.update_status(d.id, "awaiting_delegation")
            packages = build_delegation_packages(
                topic=d.topic, agents=seated, constitution=constitution,
                region_names=region_names,
            )
            need_delegate = [p for p in packages if p["needs_delegation"]]

            return {
                "mode": "delegation",
                "discussion_id": d.id,
                "topic": d.topic,
                "message": f"{len(need_delegate)} agent(s) need delegation. Use the delegate tool with each agent's system_prompt as instructions.",
                "delegation_packages": need_delegate,
                "usage_hint": (
                    "For each delegation package, call the delegate tool like this:\n"
                    "  delegate(instructions=package['system_prompt'] + '\\n\\n' + package['user_message'])\n"
                    "Then use council_conclude_discussion to record the final synthesis."
                ),
            }

        # All agents have providers — run directly
        discussion_repo.update_status(d.id, "deliberating")
        all_new = []
        for _ in range(rounds):
            prior = all_new if all_new else None
            results = await deliberate(
                topic=d.topic, agents=seated, constitution=constitution,
                region_names=region_names, prior_messages=prior,
            )
            for r in results:
                msg = discussion_repo.add_message(
                    discussion_id=d.id, agent_id=r["agent_id"],
                    agent_name=r["agent_name"], content=r["content"],
                    agent_role=r["agent_role"],
                )
                all_new.append(msg.to_dict())

        return discussion_repo.get(d.id).to_dict()

    if name == "council_conclude_discussion":
        d = discussion_repo.update_status(
            args["discussion_id"], "concluded",
            conclusion=args.get("conclusion"),
        )
        if not d:
            raise ValueError("Discussion not found")
        return d.to_dict()

    # ── Briefing ──
    if name == "council_briefing":
        from council.services.deliberation import _build_system_prompt

        all_agents = agent_repo.list_all()
        seated = [a for a in all_agents if a.seat_id]
        agent_ids = args.get("agent_ids")
        if agent_ids:
            seated = [a for a in seated if a.id in agent_ids]
        if not seated:
            raise ValueError("No seated agents available")

        constitution = constitution_repo.get_active()
        regions = region_repo.list_all()
        seats = seat_repo.list_all()
        region_names = {}
        for s in seats:
            if s.agent_id and s.region_id:
                r = next((rg for rg in regions if rg.id == s.region_id), None)
                if r:
                    region_names[s.agent_id] = r.name

        task = args["task"]
        briefings = []
        for agent in seated:
            prompt = _build_system_prompt(agent, constitution, task, region_names.get(agent.id))
            briefings.append({
                "agent_id": agent.id,
                "agent_name": agent.name,
                "agent_role": agent.role.value if hasattr(agent.role, 'value') else agent.role,
                "region": region_names.get(agent.id),
                "model_provider": agent.model_provider,
                "model_name": agent.model_name,
                "system_prompt": prompt,
                "task": task,
            })

        return {
            "task": task,
            "agent_count": len(briefings),
            "briefings": briefings,
            "usage_hint": "For each briefing, you can use the delegate tool with the system_prompt as instructions, or call council_send to have agents respond directly via their model providers.",
        }

    if name == "council_send":
        from council.services.deliberation import deliberate, check_delegation_needed, build_delegation_packages

        topic = args["task"]

        all_agents = agent_repo.list_all()
        seated = [a for a in all_agents if a.seat_id]
        if not seated:
            raise ValueError("No seated agents available")

        regions = region_repo.list_all()
        seats = seat_repo.list_all()
        region_names = {}
        for s in seats:
            if s.agent_id and s.region_id:
                r = next((rg for rg in regions if rg.id == s.region_id), None)
                if r:
                    region_names[s.agent_id] = r.name

        constitution = constitution_repo.get_active()
        rounds = args.get("rounds", 1)

        # Check if delegation is needed (no providers configured/available)
        needs_delegation = check_delegation_needed(seated)

        # Create discussion record
        d = discussion_repo.create(topic=topic)

        if needs_delegation:
            # Some or all agents need delegation — return packages for the calling LLM
            discussion_repo.update_status(d.id, "awaiting_delegation")
            packages = build_delegation_packages(
                topic=topic, agents=seated, constitution=constitution,
                region_names=region_names,
            )

            # Separate agents that can self-serve from those needing delegation
            can_call = [p for p in packages if not p["needs_delegation"]]
            need_delegate = [p for p in packages if p["needs_delegation"]]

            # If some agents CAN self-serve, run them directly
            direct_results = []
            if can_call:
                discussion_repo.update_status(d.id, "deliberating")
                callable_agents = [a for a in seated if any(p["agent_id"] == a.id for p in can_call)]
                results = await deliberate(
                    topic=topic, agents=callable_agents, constitution=constitution,
                    region_names=region_names,
                )
                for r in results:
                    if not r.get("needs_delegation"):
                        msg = discussion_repo.add_message(
                            discussion_id=d.id, agent_id=r["agent_id"],
                            agent_name=r["agent_name"], content=r["content"],
                            agent_role=r["agent_role"],
                        )
                        direct_results.append(msg.to_dict())

            return {
                "mode": "delegation",
                "discussion_id": d.id,
                "topic": topic,
                "message": f"{len(need_delegate)} agent(s) need delegation — no model provider configured or available. "
                           f"Use the delegate tool to run each agent as a subagent with their system_prompt as instructions.",
                "direct_responses": direct_results,
                "delegation_packages": need_delegate,
                "usage_hint": (
                    "For each delegation package, call the delegate tool like this:\n"
                    "  delegate(instructions=package['system_prompt'] + '\\n\\n' + package['user_message'])\n"
                    "Then use council_conclude_discussion to record the final synthesis."
                ),
            }

        # All agents have providers — run deliberation directly
        discussion_repo.update_status(d.id, "deliberating")
        all_new = []
        for _ in range(rounds):
            prior = all_new if all_new else None
            results = await deliberate(
                topic=topic, agents=seated, constitution=constitution,
                region_names=region_names, prior_messages=prior,
            )
            for r in results:
                msg = discussion_repo.add_message(
                    discussion_id=d.id, agent_id=r["agent_id"],
                    agent_name=r["agent_name"], content=r["content"],
                    agent_role=r["agent_role"],
                )
                all_new.append(msg.to_dict())

        return discussion_repo.get(d.id).to_dict()

    # ── Constitution ──
    if name == "council_get_constitution":
        active = constitution_repo.get_active()
        if not active:
            return {"active": False, "message": "No active constitution"}
        return active.to_dict()

    if name == "council_create_constitution":
        created = constitution_repo.create(
            preamble=args.get("preamble", ""),
            rules=args.get("rules", ""),
            goals=args.get("goals", ""),
            constraints=args.get("constraints", ""),
            activate=True,
        )
        return created.to_dict()

    if name == "council_list_constitutions":
        return [c.to_dict() for c in constitution_repo.list_all()]

    # ── Community ──
    if name == "council_list_members":
        cohort = args.get("cohort")
        active_only = args.get("active_only", True)
        if cohort:
            return [m.to_dict() for m in community_member_repo.get_by_cohort(cohort, active_only)]
        return [m.to_dict() for m in community_member_repo.list_all(active_only)]

    if name == "council_get_member":
        member = community_member_repo.get(args["member_id"])
        if not member:
            raise ValueError("Community member not found")
        return member.to_dict()

    if name == "council_create_member":
        from council.models.community import CommunityMember, Cohort
        member = CommunityMember(
            name=args["name"],
            cohort=Cohort(args["cohort"]),
            age=args.get("age", 35),
            profession=args.get("profession", ""),
            background=args.get("background", ""),
            passions=args.get("passions", []),
            core_values=args.get("core_values", []),
            communication_style=args.get("communication_style", ""),
            perspective_summary=args.get("perspective_summary", ""),
            is_custom=True,
        )
        created = community_member_repo.create(member)
        return created.to_dict()

    if name == "council_update_member":
        member_id = args.pop("member_id")
        updated = community_member_repo.update(member_id, **args)
        if not updated:
            raise ValueError("Community member not found")
        return updated.to_dict()

    if name == "council_delete_member":
        if not community_member_repo.delete(args["member_id"]):
            raise ValueError("Community member not found")
        return {"ok": True}

    if name == "council_focus_group":
        from council.services.community import run_focus_group

        topic = args["topic"]
        method = args.get("method", "diverse")
        size = args.get("size", 8)
        cohort_filter = args.get("cohort_filter")
        passion_filter = args.get("passion_filter")
        discussion_id = args.get("discussion_id")

        # Select members
        members = community_member_repo.select_members(
            method=method, size=size,
            cohort_filter=cohort_filter, passion_filter=passion_filter,
        )
        if not members:
            raise ValueError("No community members available for selection")

        # Create focus group record
        fg = focus_group_repo.create(
            topic=topic,
            member_ids=[m.id for m in members],
            method=method, size=size,
            discussion_id=discussion_id,
            cohort_filter=cohort_filter, passion_filter=passion_filter,
        )

        # Run the focus group
        focus_group_repo.update_status(fg.id, "active")
        result = await run_focus_group(topic=topic, members=members)

        if result.get("needs_delegation"):
            focus_group_repo.update_status(fg.id, "pending")
            return {
                "focus_group_id": fg.id,
                "mode": "delegation",
                "message": "No model provider available. Use the delegate tool with the system_prompt and user_message.",
                "members": [{"name": m.name, "cohort": m.cohort.value if hasattr(m.cohort, 'value') else m.cohort, "profession": m.profession} for m in members],
                "system_prompt": result["system_prompt"],
                "user_message": result["user_message"],
            }

        # Record responses
        for resp in result.get("responses", []):
            member = next((m for m in members if m.name == resp.get("member_name")), None)
            if member:
                focus_group_repo.add_response(
                    focus_group_id=fg.id,
                    member_id=member.id,
                    member_name=member.name,
                    position=resp.get("position", ""),
                    sentiment=float(resp.get("sentiment", 0.0)),
                    confidence=float(resp.get("confidence", 0.5)),
                    key_concern=resp.get("key_concern", ""),
                )

        fg = focus_group_repo.update_status(fg.id, "completed", synthesis=result.get("synthesis", ""))
        return fg.to_dict()

    if name == "council_poll":
        from council.services.community import run_poll

        question = args["question"]
        method = args.get("method", "all")
        discussion_id = args.get("discussion_id")

        if method == "all":
            members = community_member_repo.list_all(active_only=True)
        else:
            size = args.get("size", 60)
            members = community_member_repo.select_members(
                method=method, size=size,
                cohort_filter=args.get("cohort_filter"),
                passion_filter=args.get("passion_filter"),
            )

        if not members:
            raise ValueError("No community members available")

        poll = community_poll_repo.create(
            question=question,
            member_ids=[m.id for m in members],
            discussion_id=discussion_id,
        )

        result = await run_poll(question=question, members=members)

        if result.get("needs_delegation"):
            return {
                "poll_id": poll.id,
                "mode": "delegation",
                "message": "No model provider available. Use delegation to run the poll.",
                "system_prompt": result["system_prompt"],
                "user_message": result["user_message"],
            }

        # Record responses
        for resp in result.get("responses", []):
            member = next((m for m in members if m.name == resp.get("member_name")), None)
            if member:
                sentiment = 0.5 if resp.get("position") == "support" else (-0.5 if resp.get("position") == "oppose" else 0.0)
                community_poll_repo.add_response(
                    poll_id=poll.id,
                    member_id=member.id,
                    member_name=member.name,
                    position=resp.get("reasoning", resp.get("position", "")),
                    sentiment=sentiment,
                    key_concern=resp.get("key_concern", ""),
                )

        poll = community_poll_repo.update_results(
            poll_id=poll.id,
            support_pct=result.get("support_pct", 0.0),
            oppose_pct=result.get("oppose_pct", 0.0),
            neutral_pct=result.get("neutral_pct", 0.0),
            top_concerns=result.get("top_concerns", []),
            top_endorsements=result.get("top_endorsements", []),
            synthesis=result.get("synthesis", ""),
        )
        return poll.to_dict()

    if name == "council_town_hall":
        from council.services.community import run_town_hall

        proposal = args["proposal"]
        size = args.get("size", 20)
        members = community_member_repo.select_members(method="diverse", size=size)

        if not members:
            raise ValueError("No community members available")

        result = await run_town_hall(proposal=proposal, members=members)

        if result.get("needs_delegation"):
            return {
                "mode": "delegation",
                "message": "No model provider available. Use delegation to run the town hall.",
                "system_prompt": result["system_prompt"],
                "user_message": result["user_message"],
            }

        return {
            "proposal": proposal,
            "member_count": len(members),
            "members": [{"name": m.name, "cohort": m.cohort.value if hasattr(m.cohort, 'value') else m.cohort} for m in members],
            **result,
        }

    if name == "council_consult_member":
        from council.services.community import consult_member

        member = community_member_repo.get(args["member_id"])
        if not member:
            raise ValueError("Community member not found")

        result = await consult_member(member=member, question=args["question"])
        return result

    if name == "council_community_stats":
        return community_member_repo.get_stats()

    raise ValueError(f"Unknown tool: {name}")


# ── Main ─────────────────────────────────────────────────────────────────────

async def main():
    init_services()

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="council-governance",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
