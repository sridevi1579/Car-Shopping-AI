import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import dotenv_values
from core.mcp_client import make_mcp_session
from core.session_store import sessions
from agents.carsearch_agent import agent_chat
from agents.tradein_agent import agent_tradein

# ── Config ─────────────────────────────────────────────────────────────────────
_env = dotenv_values(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

ANTHROPIC_API_KEY   = _env.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")

BASE            = os.path.dirname(os.path.abspath(__file__))
MCP_SERVER_URL  = "http://127.0.0.1:5002/sse"
FRONTEND_OUT    = os.path.join(BASE, "frontend", "out")

app = Flask(__name__)
CORS(app)

# ── MCP client (persistent — one connection for the lifetime of this process) ──

mcp_session = make_mcp_session(MCP_SERVER_URL)


# ── Session store (SQLite-backed, survives restarts, 24h TTL) ──────────────────
# sessions imported from session_store above

# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/chat", methods=["POST"])
def chat():
    data         = request.get_json(silent=True) or {}
    user_message = data.get("message", "").strip()
    session_id   = data.get("session_id", "default")

    if not user_message:
        return jsonify({"error": "message is required"}), 400

    try:
        reply, cars = agent_chat(session_id, user_message, mcp_session)
        return jsonify({"response": reply, "cars": cars})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/reset", methods=["POST"])
def reset():
    data       = request.get_json(silent=True) or {}
    session_id = data.get("session_id", "default")
    sessions.pop("search:" + session_id)
    return jsonify({"status": "ok"})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


# ── Trade-In routes ────────────────────────────────────────────────────────────

@app.route("/estimate", methods=["POST"])
def estimate():
    data         = request.get_json(silent=True) or {}
    user_message = data.get("message", "").strip()
    session_id   = data.get("session_id", "default")

    if not user_message:
        return jsonify({"error": "message is required"}), 400

    try:
        reply, estimate_result = agent_tradein(session_id, user_message, mcp_session)
        return jsonify({"response": reply, "estimate": estimate_result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/reset-tradein", methods=["POST"])
def reset_tradein():
    data       = request.get_json(silent=True) or {}
    session_id = data.get("session_id", "default")
    sessions.pop("tradein:" + session_id)
    return jsonify({"status": "ok"})


# ── Serve static Next.js frontend ─────────────────────────────────────────────

@app.route("/")
def serve_index():
    return send_from_directory(FRONTEND_OUT, "index.html")


@app.route("/tradein")
def serve_tradein():
    return send_from_directory(FRONTEND_OUT, "tradein.html")


@app.route("/summary")
def serve_summary():
    return send_from_directory(FRONTEND_OUT, "summary.html")


@app.route("/<path:filename>")
def serve_static(filename):
    return send_from_directory(FRONTEND_OUT, filename)


if __name__ == "__main__":
    print("AutoAgent running at http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
