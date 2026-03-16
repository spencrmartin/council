"""
Community engagement service — orchestrates focus groups, polls, and consultations.

Uses the same model provider infrastructure as deliberation.py but generates
responses from community member personas rather than council agents.
"""
import json
import os
import httpx
from typing import Optional, List

from ..models.community import CommunityMember, FocusGroup, CommunityPoll, MemberResponse


# ── Provider calls (shared with deliberation) ────────────────────────────────

def _resolve_community_provider() -> tuple[str, str]:
    """
    Resolve the model provider for community engagement.
    Uses COUNCIL_DEFAULT_PROVIDER or auto-detects from API keys.
    """
    provider = os.environ.get("COUNCIL_DEFAULT_PROVIDER", "").lower().strip()
    model = os.environ.get("COUNCIL_DEFAULT_MODEL", "").strip()

    if provider:
        return provider, model

    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic", model or "claude-sonnet-4-20250514"
    if os.environ.get("OPENAI_API_KEY"):
        return "openai", model or "gpt-4o"

    return "", ""


async def _call_anthropic(model: str, system_prompt: str, user_message: str) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return "[Error: ANTHROPIC_API_KEY not set]"

    async with httpx.AsyncClient(timeout=90) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": model or "claude-sonnet-4-20250514",
                "max_tokens": 1024,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_message}],
            },
        )
        if resp.status_code != 200:
            return f"[Anthropic error {resp.status_code}: {resp.text[:200]}]"
        data = resp.json()
        return data.get("content", [{}])[0].get("text", "[No response]")


async def _call_openai(model: str, system_prompt: str, user_message: str) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return "[Error: OPENAI_API_KEY not set]"

    async with httpx.AsyncClient(timeout=90) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model or "gpt-4o",
                "max_tokens": 1024,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
            },
        )
        if resp.status_code != 200:
            return f"[OpenAI error {resp.status_code}: {resp.text[:200]}]"
        data = resp.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "[No response]")


async def _call_provider(system_prompt: str, user_message: str) -> Optional[str]:
    """Call the resolved provider. Returns None if no provider available."""
    provider, model = _resolve_community_provider()
    if provider == "anthropic":
        return await _call_anthropic(model, system_prompt, user_message)
    elif provider == "openai":
        return await _call_openai(model, system_prompt, user_message)
    elif not provider:
        return None
    else:
        return f"[Unknown provider '{provider}']"


# ── Focus Group Engagement ───────────────────────────────────────────────────

def _build_focus_group_system_prompt(members: List[CommunityMember], topic: str) -> str:
    """Build a system prompt that simulates a focus group discussion."""
    parts = [
        "You are simulating a focus group discussion among community members.",
        "Each member has a distinct personality, background, and perspective.",
        "Generate authentic responses that reflect each member's unique voice.",
        "",
        "IMPORTANT: Respond with a JSON object containing an array of member responses.",
        "Each response must include the member's perspective, sentiment (-1 to 1),",
        "confidence (0 to 1), and a one-line key concern.",
        "",
        "The members in this focus group are:",
        "",
    ]

    for m in members:
        parts.append(f"--- {m.name} ---")
        parts.append(m.build_persona_prompt())
        parts.append("")

    parts.append("Respond ONLY with valid JSON in this exact format:")
    parts.append("""{
  "responses": [
    {
      "member_name": "Name",
      "position": "Their 2-4 sentence perspective on the topic",
      "sentiment": 0.5,
      "confidence": 0.8,
      "key_concern": "One-line summary of their main point"
    }
  ],
  "synthesis": "A 2-3 sentence synthesis of the group's overall perspective, noting areas of agreement and disagreement."
}""")

    return "\n".join(parts)


async def run_focus_group(
    topic: str,
    members: List[CommunityMember],
) -> dict:
    """
    Run a focus group discussion and return structured responses.

    Returns:
        {
            "responses": [{"member_name", "position", "sentiment", "confidence", "key_concern"}, ...],
            "synthesis": "...",
            "needs_delegation": bool,
            "system_prompt": str (if delegation needed),
            "user_message": str (if delegation needed),
        }
    """
    system_prompt = _build_focus_group_system_prompt(members, topic)
    user_message = f"TOPIC FOR DISCUSSION: {topic}\n\nPlease simulate each member's response to this topic, staying true to their unique perspective and communication style."

    result = await _call_provider(system_prompt, user_message)

    if result is None:
        # No provider — return delegation package
        return {
            "needs_delegation": True,
            "system_prompt": system_prompt,
            "user_message": user_message,
            "responses": [],
            "synthesis": "",
        }

    # Parse the JSON response
    try:
        # Try to extract JSON from the response (handle markdown code blocks)
        json_str = result
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()

        parsed = json.loads(json_str)
        return {
            "needs_delegation": False,
            "responses": parsed.get("responses", []),
            "synthesis": parsed.get("synthesis", ""),
        }
    except (json.JSONDecodeError, IndexError):
        # If JSON parsing fails, return the raw text as synthesis
        return {
            "needs_delegation": False,
            "responses": [],
            "synthesis": result,
            "parse_error": "Could not parse structured responses, raw text returned as synthesis.",
        }


# ── Poll Engagement ──────────────────────────────────────────────────────────

def _build_poll_system_prompt(members: List[CommunityMember], question: str) -> str:
    """Build a system prompt for polling community members."""
    parts = [
        "You are simulating a poll across community members.",
        "Each member votes based on their unique perspective and values.",
        "Generate authentic responses that reflect each member's worldview.",
        "",
        f"There are {len(members)} members being polled.",
        "",
        "The members are:",
        "",
    ]

    for m in members:
        parts.append(f"- {m.name} ({m.profession}, {m.cohort.value if hasattr(m.cohort, 'value') else m.cohort}): {m.perspective_summary[:100]}")

    parts.append("")
    parts.append("Respond ONLY with valid JSON in this exact format:")
    parts.append("""{
  "responses": [
    {
      "member_name": "Name",
      "position": "support" | "oppose" | "neutral",
      "reasoning": "One sentence explaining their position",
      "key_concern": "Their main concern or endorsement"
    }
  ],
  "support_pct": 65.0,
  "oppose_pct": 25.0,
  "neutral_pct": 10.0,
  "top_concerns": ["concern 1", "concern 2", "concern 3"],
  "top_endorsements": ["endorsement 1", "endorsement 2"],
  "synthesis": "2-3 sentence summary of the poll results."
}""")

    return "\n".join(parts)


async def run_poll(
    question: str,
    members: List[CommunityMember],
) -> dict:
    """
    Run a poll across community members.

    Returns structured poll results or a delegation package.
    """
    system_prompt = _build_poll_system_prompt(members, question)
    user_message = f"POLL QUESTION: {question}\n\nPlease simulate each member's vote and reasoning based on their unique perspective."

    result = await _call_provider(system_prompt, user_message)

    if result is None:
        return {
            "needs_delegation": True,
            "system_prompt": system_prompt,
            "user_message": user_message,
        }

    try:
        json_str = result
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()

        parsed = json.loads(json_str)
        return {
            "needs_delegation": False,
            **parsed,
        }
    except (json.JSONDecodeError, IndexError):
        return {
            "needs_delegation": False,
            "responses": [],
            "synthesis": result,
            "parse_error": "Could not parse structured poll results.",
        }


# ── Individual Consultation ──────────────────────────────────────────────────

def _build_consultation_prompt(member: CommunityMember) -> str:
    """Build a system prompt for a deep-dive consultation with one member."""
    parts = [
        "You are role-playing as a specific community member in a one-on-one consultation.",
        "Stay completely in character. Respond as this person would — with their voice,",
        "their concerns, their communication style, and their values.",
        "",
        member.build_persona_prompt(),
        "",
        "Respond naturally and conversationally, as if you're having a real discussion.",
        "Keep responses under 150 words but make them substantive.",
    ]
    return "\n".join(parts)


async def consult_member(
    member: CommunityMember,
    question: str,
) -> dict:
    """
    Have a deep-dive consultation with a specific community member.

    Returns their response or a delegation package.
    """
    system_prompt = _build_consultation_prompt(member)
    user_message = question

    result = await _call_provider(system_prompt, user_message)

    if result is None:
        return {
            "needs_delegation": True,
            "member": member.to_dict(),
            "system_prompt": system_prompt,
            "user_message": user_message,
        }

    return {
        "needs_delegation": False,
        "member": member.to_dict(),
        "response": result,
    }


# ── Town Hall ────────────────────────────────────────────────────────────────

def _build_town_hall_prompt(members: List[CommunityMember], proposal: str) -> str:
    """Build a prompt for a town hall reaction to a council proposal."""
    parts = [
        "You are simulating a town hall meeting where community members react to a council proposal.",
        "This is more free-form than a focus group — members can agree, disagree, build on each other's points,",
        "raise concerns, ask questions, or express support.",
        "",
        f"There are {len(members)} community members present.",
        "",
    ]

    for m in members:
        parts.append(f"--- {m.name} ({m.profession}) ---")
        parts.append(f"Cohort: {m.cohort.value if hasattr(m.cohort, 'value') else m.cohort}")
        parts.append(f"Values: {', '.join(m.core_values[:3])}")
        parts.append(f"Style: {m.communication_style[:80]}")
        parts.append("")

    parts.append("Respond ONLY with valid JSON:")
    parts.append("""{
  "reactions": [
    {
      "member_name": "Name",
      "reaction_type": "support" | "concern" | "question" | "amendment" | "opposition",
      "statement": "Their 1-3 sentence reaction",
      "emotion": "enthusiastic" | "cautious" | "worried" | "neutral" | "frustrated" | "hopeful"
    }
  ],
  "overall_sentiment": 0.3,
  "key_themes": ["theme 1", "theme 2", "theme 3"],
  "synthesis": "3-4 sentence summary of the town hall reaction, noting the overall mood and key points of contention."
}""")

    return "\n".join(parts)


async def run_town_hall(
    proposal: str,
    members: List[CommunityMember],
) -> dict:
    """
    Run a town hall where community members react to a proposal.
    """
    system_prompt = _build_town_hall_prompt(members, proposal)
    user_message = f"COUNCIL PROPOSAL: {proposal}\n\nPlease simulate each community member's reaction to this proposal."

    result = await _call_provider(system_prompt, user_message)

    if result is None:
        return {
            "needs_delegation": True,
            "system_prompt": system_prompt,
            "user_message": user_message,
        }

    try:
        json_str = result
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()

        parsed = json.loads(json_str)
        return {
            "needs_delegation": False,
            **parsed,
        }
    except (json.JSONDecodeError, IndexError):
        return {
            "needs_delegation": False,
            "reactions": [],
            "synthesis": result,
            "parse_error": "Could not parse structured town hall results.",
        }
