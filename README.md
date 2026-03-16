# Council — Agent Governance Visualization

A visual council for managing AI agent governance. Agents sit in councilary seats, organized into regions that define their responsibilities for specific inputs and outputs.

## Architecture

Follows the same patterns as [Brian](https://github.com/spencrmartin/brian):

| Layer | Tech | Purpose |
|-------|------|---------|
| `council/` | Python / FastAPI / SQLite | Backend API + database |
| `council_mcp/` | MCP (stdio) | Expose council tools to AI assistants |
| `frontend/` | React / Vite / Tailwind / D3 | Council visualization UI |
| `src-tauri/` | Rust / Tauri v2 | Desktop app wrapper |

## Concepts

- **Agent** — An AI agent that occupies a seat in the council
- **Seat** — A position in the hemicycle layout; agents are assigned to seats
- **Region** — A named group of seats with defined input/output responsibilities
- **Input** — A data source or signal that a region is responsible for processing
- **Output** — An action, decision, or artifact that a region produces

## Quick Start

```bash
# Backend
cd council && pip install -e . && python -m council.main

# Frontend
cd frontend && pnpm install && pnpm dev

# MCP Server (for AI assistants)
python -m council_mcp.server
```

## Development

```bash
# Run backend in dev mode
cd council && python -m council.main

# Run frontend in dev mode (proxies API to backend)
cd frontend && pnpm dev
```
