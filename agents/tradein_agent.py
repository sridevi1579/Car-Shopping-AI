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

BASE           = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MCP_SERVER_URL = "http://127.0.0.1:5002/sse"

# ── Load AI client ─────────────────────────────────────────────────────────────

import anthropic
ai_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


MAX_AGENT_TURNS = 10  # safety cap — prevents infinite loops if Claude misbehaves


# ── System prompt ──────────────────────────────────────────────────────────────

def load_system_prompt():
    rules = open(os.path.join(BASE, "prompts", "TRADEIN_RULES.md"), encoding="utf-8").read()
    return (
        rules +
        "\n\nCRITICAL OUTPUT RULE: After calling estimate_trade_in, write ONLY a brief "
        "1-2 sentence summary of the result (e.g. 'Your 2020 Honda Civic is worth ~$16,200 as a trade-in.'). "
        "Do NOT paste raw JSON or repeat all fields — the UI renders the full estimate card automatically. "
        "Then always ask if they want to explore financing with the trade-in applied as a down payment."
    )

SYSTEM_PROMPT = load_system_prompt()


# ── History trimming ──────────────────────────────────────────────────────────

RECENT_MSGS = 6   # trade-in flow is shorter, needs less history


# ── Tool definitions ───────────────────────────────────────────────────────────

CLAUDE_TOOLS = [
    {
        "name": "estimate_trade_in",
        "description": "Estimate the trade-in value of a user's car based on make, model, year, mileage and condition",
        "input_schema": {
            "type": "object",
            "properties": {
                "make":      {"type": "string",  "description": "Car brand e.g. Honda, Toyota"},
                "model":     {"type": "string",  "description": "Car model e.g. Civic, Camry"},
                "year":      {"type": "integer", "description": "Year of the car e.g. 2020"},
                "mileage":   {"type": "integer", "description": "Current mileage e.g. 35000"},
                "condition": {"type": "string",  "description": "Condition: Excellent, Good, Fair, or Poor"},
                "trim":      {"type": "string",  "description": "Trim level (optional)"},
                "location":  {"type": "string",  "description": "City in Arizona"}
            },
            "required": ["make", "model", "year", "mileage", "condition"]
        }
    }
]

# ── Agent loop ─────────────────────────────────────────────────────────────────

def agent_tradein_claude(session_id: str, user_message: str, mcp_session) -> tuple:
    history = sessions.get("tradein:" + session_id) or []
    history.append({"role": "user", "content": user_message})
    last_estimate = {}

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
            tool_result = mcp_session.call_tool("estimate_trade_in", tool_use.input)
            last_estimate = tool_result

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
            sessions.save("tradein:" + session_id, history)
            return final_text, last_estimate

    sessions.save("tradein:" + session_id, history)
    raise RuntimeError("Trade-in agent exceeded maximum turns without a final response.")


def agent_tradein(session_id: str, user_message: str, mcp_session) -> tuple:
    return agent_tradein_claude(session_id, user_message, mcp_session)


# ── Standalone mode ────────────────────────────────────────────────────────────
# Run this file directly to start the trade-in agent as its own server.
# When imported by app.py, none of this block executes.

if __name__ == "__main__":
    from flask import Flask, request, jsonify
    from flask_cors import CORS
    from core.mcp_client import make_mcp_session

    _mcp_session = make_mcp_session(MCP_SERVER_URL)

    app = Flask(__name__)
    CORS(app)

    @app.route("/estimate", methods=["POST"])
    def estimate():
        data         = request.get_json(silent=True) or {}
        user_message = data.get("message", "").strip()
        session_id   = data.get("session_id", "default")

        if not user_message:
            return jsonify({"error": "message is required"}), 400

        try:
            reply, estimate_result = agent_tradein(session_id, user_message, _mcp_session)
            return jsonify({"response": reply, "estimate": estimate_result})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/reset", methods=["POST"])
    def reset():
        data       = request.get_json(silent=True) or {}
        session_id = data.get("session_id", "default")
        sessions.pop("tradein:" + session_id)
        return jsonify({"status": "ok"})

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "agent": "trade-in-estimator"})

    print("Trade-In Agent running at http://localhost:5001")
    app.run(host="0.0.0.0", port=5001, debug=False)
