"""
agent_utils.py — Shared utilities for all AI agents.

Single source of truth for logic used by both app.py and tradein_agent.py.
Fix it here once — both agents get the fix automatically.
"""


def trim_for_api(history: list, recent_msgs: int) -> list:
    """Smart trim — preserves chronological order (required by Claude API):
    - Tool use + tool result pairs always kept (search/estimate data is critical)
    - Last recent_msgs messages always kept
    - Merged back in original order so API never sees out-of-sequence messages
    Full history stays in memory — only the API call is trimmed.
    """
    system = [m for m in history if m.get("role") == "system"]
    rest   = [m for m in history if m.get("role") != "system"]

    # Mark which indices are tool-related (must always keep)
    tool_indices = set()
    for i, m in enumerate(rest):
        content = m.get("content", "")
        if isinstance(content, list) or m.get("role") == "tool":
            tool_indices.add(i)

    # Also keep the last recent_msgs messages regardless of type
    keep_indices = tool_indices | set(range(max(0, len(rest) - recent_msgs), len(rest)))

    # Rebuild in original order — no reordering, no gaps
    return system + [m for i, m in enumerate(rest) if i in keep_indices]
