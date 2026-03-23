import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import dotenv_values
from core.agent_utils import trim_for_api
from core.session_store import sessions

# ── Config ─────────────────────────────────────────────────────────────────────

_env = dotenv_values(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

ANTHROPIC_API_KEY = _env.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Load AI client ─────────────────────────────────────────────────────────────

import anthropic
ai_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ── Constants ──────────────────────────────────────────────────────────────────

RECENT_MSGS     = 8   # last N conversational messages to keep
MAX_AGENT_TURNS = 10  # safety cap — prevents infinite loops if Claude misbehaves

# ── System prompt ──────────────────────────────────────────────────────────────

def load_system_prompt():
    rules     = open(os.path.join(BASE, "prompts", "CARSEARCH_RULES.md"),   encoding="utf-8").read()
    prompts   = open(os.path.join(BASE, "prompts", "CARSEARCH_PROMPTS.md"), encoding="utf-8").read()
    financing = open(os.path.join(BASE, "prompts", "Financing.md"), encoding="utf-8").read()
    return (
        rules + "\n\n" +
        prompts + "\n\n" +
        financing +
        "\n\nCRITICAL: Only show data returned by the search_cars tool. "
        "Never add engine specs, transmission, fuel economy, pros/cons, or any details "
        "not in the tool results. If a field is missing say 'Not available'."
    )

SYSTEM_PROMPT = load_system_prompt()

# ── Tool definitions ───────────────────────────────────────────────────────────

CLAUDE_TOOLS = [
    {
        "name": "search_cars",
        "description": "Search for cheapest cars across Carvana, CarMax and CarGurus based on user preferences",
        "input_schema": {
            "type": "object",
            "properties": {
                "make":        {"type": "string",  "description": "Car brand e.g. Honda, Toyota"},
                "model":       {"type": "string",  "description": "Car model e.g. Civic, Camry"},
                "year":        {"type": "string",  "description": "Year or year range e.g. 2020 or 2018-2022"},
                "budget":      {"type": "integer", "description": "Maximum price in dollars"},
                "max_mileage": {"type": "integer", "description": "Maximum mileage"},
                "condition":   {"type": "string",  "description": "new or used"},
                "location":    {"type": "string",  "description": "City to search in"}
            },
            "required": []
        }
    },
    {
        "name": "estimate_trade_in",
        "description": "Estimate the trade-in value of the user's current car. Use this when the user mentions they have a car to trade in — the value is added to their search budget to give an effective budget.",
        "input_schema": {
            "type": "object",
            "properties": {
                "make":      {"type": "string",  "description": "Trade-in car brand e.g. Honda, Toyota"},
                "model":     {"type": "string",  "description": "Trade-in car model e.g. Civic, Camry"},
                "year":      {"type": "integer", "description": "Trade-in car year e.g. 2019"},
                "mileage":   {"type": "integer", "description": "Current mileage on the trade-in car"},
                "condition": {"type": "string",  "description": "Car condition: excellent, good, fair, or poor"},
                "trim":      {"type": "string",  "description": "Trim level e.g. LX, EX (optional)"},
                "location":  {"type": "string",  "description": "City (optional)"}
            },
            "required": ["make", "model", "year", "mileage", "condition"]
        }
    }
]

# ── Agent loop ─────────────────────────────────────────────────────────────────

def agent_chat_claude(session_id: str, user_message: str, mcp_session) -> tuple:
    history = sessions.get("search:" + session_id) or []
    history.append({"role": "user", "content": user_message})
    last_cars = []

    for _ in range(MAX_AGENT_TURNS):
        response = ai_client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=CLAUDE_TOOLS,
            messages=trim_for_api(history, RECENT_MSGS)
        )

        if response.stop_reason == "tool_use":
            tool_use    = next(b for b in response.content if b.type == "tool_use")
            tool_result = mcp_session.call_tool(tool_use.name, tool_use.input)

            if tool_use.name == "search_cars":
                last_cars = [
                    {k: (int(v) if hasattr(v, "item") else v) for k, v in car.items()}
                    for car in tool_result[:4]
                ]

            history.append({"role": "assistant", "content": response.content})
            history.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": json.dumps(tool_result)
                }]
            })
        else:
            final_text = next(b.text for b in response.content if hasattr(b, "text"))
            history.append({"role": "assistant", "content": final_text})
            sessions.save("search:" + session_id, history)
            return final_text, last_cars

    sessions.save("search:" + session_id, history)
    raise RuntimeError("Car search agent exceeded maximum turns without a final response.")


def agent_chat(session_id: str, user_message: str, mcp_session) -> tuple:
    return agent_chat_claude(session_id, user_message, mcp_session)
