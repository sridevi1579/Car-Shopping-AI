# Car Shopping AI Agent

> A full-stack conversational AI assistant that guides users through the entire car buying journey — from finding the right vehicle to estimating trade-in value and calculating financing — powered by Claude AI and the Model Context Protocol (MCP).

**Demo:** [Watch on YouTube](https://youtu.be/jnjvCwLHF9I)

---

## Overview

Buying a car online means solving two problems at once: making complex decisions (financing, trade-ins) feel simple, while building enough trust to close a deal on something the customer has never seen in person. This project tackles both.

Two specialized AI agents handle distinct parts of the journey with separate system prompts and isolated conversation histories. An MCP server sits between the agents and the data layer, keeping tool calls fast and the architecture clean.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│               Next.js Frontend (TypeScript)              │
│     Car Finder  │  Trade-In Estimator  │  Deal Summary  │
└─────────────────────────────────────────────────────────┘
                         │ HTTP
┌─────────────────────────────────────────────────────────┐
│                  Flask API (Python)                      │
│  ┌─────────────────────┐   ┌──────────────────────────┐ │
│  │  Car Search Agent   │   │   Trade-In Agent         │ │
│  │  (agentic loop)     │   │   (estimation flow)      │ │
│  └─────────────────────┘   └──────────────────────────┘ │
│              │  SQLite session store (24h TTL)           │
└─────────────────────────────────────────────────────────┘
                         │ SSE
┌─────────────────────────────────────────────────────────┐
│              FastMCP Server (Python)                     │
│    search_cars()  │  estimate_trade_in()                │
│              │ SQLite inventory DB                       │
└─────────────────────────────────────────────────────────┘
                         │
┌─────────────────────────────────────────────────────────┐
│              External APIs                               │
│  NHTSA Safety Ratings  │  fueleconomy.gov  │  Carvana  │
└─────────────────────────────────────────────────────────┘
```

**Request flow:** User message → Flask → Agent (Claude + tools) → MCP server → SQLite + external APIs → enriched result → Claude final response → frontend.

---

## Key Technical Decisions

### Two Agents, Not One
Splitting into a Car Search Agent and a Trade-In Agent keeps system prompts focused and conversation histories clean. A single agent would conflate search context with trade-in context, degrading response quality over multi-turn conversations.

### Persistent MCP Connection
Instead of spawning a new subprocess per tool call (which adds cold-start latency), a single async MCP `ClientSession` is opened at startup in a daemon thread and reused across all requests. A threading lock serializes concurrent access, making the connection safe under load.

### Deal Scoring Algorithm
Cars are ranked using a weighted score across three signals:
| Factor | Weight |
|--------|--------|
| Price (vs. budget) | 50% |
| Mileage | 30% |
| Model year | 20% |

Top results are enriched with NHTSA safety ratings and fueleconomy.gov MPG data before being returned.

### Smart History Trimming
`trim_for_api()` preserves tool/result pairs (which Claude needs for coherent reasoning) and recent conversational turns while discarding old messages to stay within the API context window. This maintains response quality without bloating token usage.

### SQLite-Backed Session Persistence
Conversation histories are stored in SQLite with WAL mode for concurrency and a 24-hour TTL. Sessions are namespaced (`search:{id}` vs `tradein:{id}`) so both agents share one table without collision.

---

## Features

- **Conversational car search** — ask naturally ("I want a reliable Honda under $20k with low miles")
- **Inline comparison** — side-by-side car cards with safety ratings, fuel economy, and deal score
- **Financing calculator** — income-aware options across 36/48/60-month loan terms at APR
- **Trade-in estimation** — condition multiplier + mileage adjustment model with market demand factor
- **Deal summary** — full vehicle specs, trade-in deduction, financed amount, and monthly payments
- **Session memory** — conversation history persisted across page navigation

---

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| AI / Agents | Claude API (`claude-haiku-4-5`), Anthropic Python SDK |
| MCP Server | FastMCP (SSE transport) |
| Backend | Python, Flask, asyncio, threading |
| Database | SQLite (WAL mode), raw SQL |
| External APIs | NHTSA, fueleconomy.gov |
| Frontend | Next.js 14, React 18, TypeScript, Tailwind CSS |
| State Management | React Context API |

---

## Project Structure

```
├── agents/
│   ├── carsearch_agent.py    # Agentic loop for car search (up to 10 turns, top 4 results)
│   └── tradein_agent.py      # Trade-in estimation agent
├── core/
│   ├── agent_utils.py        # Smart message history trimming
│   ├── mcp_client.py         # Persistent async MCP client with threading lock
│   └── session_store.py      # SQLite session persistence with 24h TTL
├── mcp_server/
│   └── server.py             # FastMCP server exposing search_cars and estimate_trade_in
├── tools/
│   └── carapis_tool.py       # SQLite queries, deal scoring, NHTSA/fuel enrichment
├── frontend/
│   ├── app/                  # Next.js pages (car finder, trade-in, summary)
│   ├── components/           # Chat UI, car result cards, trade-in card
│   └── context/              # AppContext (shared state across pages)
├── prompts/                  # System prompt rules for each agent
├── data/                     # SQLite databases (inventory, sessions)
├── app.py                    # Flask API server
└── start.py                  # Multi-process orchestrator (builds frontend, starts MCP + Flask)
```

---

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- Anthropic API key

### Setup

```bash
# Clone the repo
git clone https://github.com/sridevi1579/Car-Shopping-AI.git
cd Car-Shopping-AI

# Install Python dependencies
pip install -r requirements.txt

# Set your API key
export ANTHROPIC_API_KEY=your_key_here

# Start everything (builds frontend, launches MCP server + Flask)
python start.py
```

Open [http://localhost:5000](http://localhost:5000)

---

## Demo

[![Car Shopping AI Demo](https://img.youtube.com/vi/jnjvCwLHF9I/maxresdefault.jpg)](https://youtu.be/jnjvCwLHF9I)

---

*Built by [Sridevi Chindalur](https://github.com/sridevi1579)*
