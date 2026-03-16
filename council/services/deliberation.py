"""
Deliberation service — orchestrates agent discussions.

Given a topic, this service:
1. Loads the active constitution as the governance context
2. For each seated agent, builds a role-specific system prompt
3. Calls the agent's configured model provider (or falls back to defaults)
4. Records responses as discussion messages
5. If no provider is available, returns delegation packages for the calling LLM

Supports: anthropic, openai, ollama (via their HTTP APIs).
Fallback: COUNCIL_DEFAULT_PROVIDER / COUNCIL_DEFAULT_MODEL env vars.
Delegation: When no provider is available at all, returns briefing packages
           so the calling LLM can spin up subagents via the delegate tool.
"""
import json
import os
import httpx
from typing import Optional, List

from ..models.agent import Agent
from ..models.constitution import Constitution
from ..models.discussion import Discussion


def _build_system_prompt(agent: Agent, constitution: Optional[Constitution], topic: str, region_name: str = None) -> str:
    """Build a system prompt for an agent based on their role and the constitution."""
    parts = []

    role_str = agent.role if isinstance(agent.role, str) else agent.role.value
    parts.append(f"You are {agent.name}, a council agent with the role of {role_str}.")

    if agent.description:
        parts.append(f"Your specialty: {agent.description}")

    if region_name:
        parts.append(f"You are assigned to the '{region_name}' region of the council.")

    if constitution:
        parts.append("\n--- COUNCIL CONSTITUTION ---")
        if constitution.preamble:
            parts.append(f"Preamble: {constitution.preamble}")
        if constitution.rules:
            parts.append(f"Rules:\n{constitution.rules}")
        if constitution.goals:
            parts.append(f"Goals:\n{constitution.goals}")
        if constitution.constraints:
            parts.append(f"Constraints:\n{constitution.constraints}")
        parts.append("--- END CONSTITUTION ---\n")

    parts.append("You are participating in a council discussion. Respond thoughtfully and concisely from your role's perspective.")
    parts.append("Keep your response focused and under 200 words.")

    return "\n".join(parts)


def _resolve_provider(agent: Agent) -> tuple[str, str]:
    """
    Resolve the model provider and model name for an agent.

    Priority:
    1. Agent's own model_provider / model_name
    2. COUNCIL_DEFAULT_PROVIDER / COUNCIL_DEFAULT_MODEL env vars
    3. Auto-detect from available API keys (ANTHROPIC_API_KEY → anthropic, OPENAI_API_KEY → openai)
    4. Returns ("", "") if nothing is available — triggers delegation mode
    """
    provider = (agent.model_provider or "").lower().strip()
    model = (agent.model_name or "").strip()

    # If agent has explicit config, use it
    if provider:
        return provider, model

    # Check for council-level defaults
    default_provider = os.environ.get("COUNCIL_DEFAULT_PROVIDER", "").lower().strip()
    default_model = os.environ.get("COUNCIL_DEFAULT_MODEL", "").strip()
    if default_provider:
        return default_provider, model or default_model

    # Auto-detect from available API keys
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic", model or default_model or "claude-sonnet-4-20250514"
    if os.environ.get("OPENAI_API_KEY"):
        return "openai", model or default_model or "gpt-4o"

    # Nothing available — delegation mode
    return "", ""


async def _call_anthropic(model: str, system_prompt: str, user_message: str) -> str:
    """Call Anthropic's Messages API."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return "[Error: ANTHROPIC_API_KEY not set]"

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": model or "claude-sonnet-4-20250514",
                "max_tokens": 512,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_message}],
            },
        )
        if resp.status_code != 200:
            return f"[Anthropic error {resp.status_code}: {resp.text[:200]}]"
        data = resp.json()
        return data.get("content", [{}])[0].get("text", "[No response]")


async def _call_openai(model: str, system_prompt: str, user_message: str) -> str:
    """Call OpenAI's Chat Completions API."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return "[Error: OPENAI_API_KEY not set]"

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model or "gpt-4o",
                "max_tokens": 512,
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


async def _call_ollama(model: str, system_prompt: str, user_message: str) -> str:
    """Call local Ollama API."""
    base_url = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"{base_url}/api/chat",
            json={
                "model": model or "llama3.2",
                "stream": False,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
            },
        )
        if resp.status_code != 200:
            return f"[Ollama error {resp.status_code}: {resp.text[:200]}]"
        data = resp.json()
        return data.get("message", {}).get("content", "[No response]")


async def _call_agent(agent: Agent, system_prompt: str, user_message: str) -> str:
    """Route to the correct provider based on agent config, with fallback chain."""
    provider, model = _resolve_provider(agent)

    if provider == "anthropic":
        return await _call_anthropic(model, system_prompt, user_message)
    elif provider == "openai":
        return await _call_openai(model, system_prompt, user_message)
    elif provider in ("ollama", "local"):
        return await _call_ollama(model, system_prompt, user_message)
    elif provider == "google":
        return f"[Google provider not yet implemented — agent {agent.name} skipped]"
    elif provider == "":
        # No provider available — return sentinel for delegation mode
        return None
    else:
        return f"[Unknown provider '{provider}' for agent {agent.name}]"


def check_delegation_needed(agents: List[Agent]) -> bool:
    """
    Check if any agents require delegation (no provider resolvable).
    Returns True if at least one agent has no provider and no fallback is available.
    """
    for agent in agents:
        provider, _ = _resolve_provider(agent)
        if not provider:
            return True
    return False


def build_delegation_packages(
    topic: str,
    agents: List[Agent],
    constitution: Optional[Constitution] = None,
    region_names: dict = None,
    prior_messages: List[dict] = None,
) -> List[dict]:
    """
    Build delegation packages for agents that need to be invoked via subagents.

    Returns a list of dicts with system_prompt, user_message, and agent metadata
    that can be passed to the delegate tool.
    """
    region_names = region_names or {}
    packages = []

    # Build the user message
    user_parts = [f"TOPIC FOR DISCUSSION: {topic}"]
    if prior_messages:
        user_parts.append("\n--- PRIOR DISCUSSION ---")
        for msg in prior_messages:
            user_parts.append(f"[{msg['agent_name']} ({msg.get('agent_role', 'agent')})] {msg['content']}")
        user_parts.append("--- END PRIOR DISCUSSION ---\n")
        user_parts.append("Please respond to the topic considering the discussion so far.")
    else:
        user_parts.append("Please share your perspective on this topic from your role in the council.")

    user_message = "\n".join(user_parts)

    for agent in agents:
        provider, model = _resolve_provider(agent)
        system_prompt = _build_system_prompt(
            agent, constitution, topic,
            region_name=region_names.get(agent.id),
        )

        package = {
            "agent_id": agent.id,
            "agent_name": agent.name,
            "agent_role": agent.role if isinstance(agent.role, str) else agent.role.value,
            "region": region_names.get(agent.id),
            "needs_delegation": not bool(provider),
            "system_prompt": system_prompt,
            "user_message": user_message,
        }

        # Include model hints if the agent has them (even if provider needs delegation)
        if agent.model_provider:
            package["model_provider"] = agent.model_provider
        if agent.model_name:
            package["model_name"] = agent.model_name

        packages.append(package)

    return packages


async def deliberate(
    topic: str,
    agents: List[Agent],
    constitution: Optional[Constitution] = None,
    region_names: dict = None,
    prior_messages: List[dict] = None,
) -> List[dict]:
    """
    Run a round of deliberation: each agent responds to the topic.

    If an agent has a configured provider (or a fallback is available), it calls
    the model directly. If not, the agent's result is marked with
    needs_delegation=True and includes the system_prompt + user_message for
    the calling LLM to invoke via the delegate tool.

    Returns a list of dicts. Each dict contains:
    - agent_id, agent_name, agent_role, content (if model responded)
    - agent_id, agent_name, agent_role, needs_delegation, system_prompt, user_message (if delegation needed)
    """
    region_names = region_names or {}
    results = []

    # Build the user message including any prior discussion context
    user_parts = [f"TOPIC FOR DISCUSSION: {topic}"]
    if prior_messages:
        user_parts.append("\n--- PRIOR DISCUSSION ---")
        for msg in prior_messages:
            user_parts.append(f"[{msg['agent_name']} ({msg.get('agent_role', 'agent')})] {msg['content']}")
        user_parts.append("--- END PRIOR DISCUSSION ---\n")
        user_parts.append("Please respond to the topic considering the discussion so far.")
    else:
        user_parts.append("Please share your perspective on this topic from your role in the council.")

    user_message = "\n".join(user_parts)

    for agent in agents:
        system_prompt = _build_system_prompt(
            agent, constitution, topic,
            region_name=region_names.get(agent.id),
        )
        content = await _call_agent(agent, system_prompt, user_message)

        if content is None:
            # Agent needs delegation — return package for calling LLM
            results.append({
                "agent_id": agent.id,
                "agent_name": agent.name,
                "agent_role": agent.role if isinstance(agent.role, str) else agent.role.value,
                "needs_delegation": True,
                "system_prompt": system_prompt,
                "user_message": user_message,
                "content": f"[DELEGATION REQUIRED] Agent '{agent.name}' has no model provider configured. "
                           f"Use the delegate tool with the system_prompt as instructions and user_message as the task. "
                           f"The agent's response should be recorded back to the discussion.",
            })
        else:
            results.append({
                "agent_id": agent.id,
                "agent_name": agent.name,
                "agent_role": agent.role if isinstance(agent.role, str) else agent.role.value,
                "needs_delegation": False,
                "content": content,
            })

    return results
