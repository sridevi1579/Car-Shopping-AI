"""
mcp_client.py — Persistent MCP session.

Connects to the shared MCP server (running over SSE/HTTP) once and keeps
the connection alive for the lifetime of the process.

Every tool call reuses the same ClientSession — both agents share one
MCP server process instead of each spawning their own subprocess.
"""

import asyncio
import json
import threading
from contextlib import AsyncExitStack

from mcp import ClientSession
from mcp.client.sse import sse_client


class _MCPSession:
    """
    Single persistent MCP ClientSession connected to the shared SSE server.

    One connection is opened at construction time and held open permanently
    via AsyncExitStack. All tool calls reuse that session.

    Thread-safe: a lock serialises concurrent calls (MCP is request/response).
    """

    def __init__(self, server_url: str) -> None:
        self._lock    = threading.Lock()
        self._loop    = asyncio.new_event_loop()
        self._session = None          # set in _connect()
        self._stack   = AsyncExitStack()

        # Dedicated daemon thread keeps the event loop alive permanently.
        # Daemon=True means it is killed automatically when the main process exits.
        t = threading.Thread(target=self._loop.run_forever, daemon=True)
        t.start()

        # Block the calling thread until the session is ready (≤ 60 s).
        # _connect retries internally so this covers the full retry window.
        future = asyncio.run_coroutine_threadsafe(
            self._connect(server_url), self._loop
        )
        future.result(timeout=60)

        print(f"[MCP] Persistent session ready -> {server_url}")

    # ── async internals ───────────────────────────────────────────────────────

    async def _connect(self, server_url: str) -> None:
        """Connect to the SSE MCP server. Retries every second for up to 30 s
        so Flask doesn't crash if the MCP server is still starting up."""
        last_exc = None
        for attempt in range(30):
            try:
                read, write = await self._stack.enter_async_context(
                    sse_client(server_url)
                )
                break                              # connected — exit retry loop
            except Exception as exc:
                last_exc = exc
                print(f"[MCP] Waiting for server... ({attempt + 1}/30)")
                await asyncio.sleep(1)
        else:
            raise last_exc                         # all 30 attempts failed

        session = await self._stack.enter_async_context(
            ClientSession(read, write)
        )
        await session.initialize()
        self._session = session

    # ── public API ────────────────────────────────────────────────────────────

    def call_tool(self, tool_name: str, tool_input: dict):
        """
        Call an MCP tool synchronously from any thread.

        The lock ensures only one call runs at a time — MCP is
        strictly request/response and does not support concurrent calls.
        """
        with self._lock:
            future = asyncio.run_coroutine_threadsafe(
                self._session.call_tool(tool_name, tool_input),
                self._loop,
            )
            result = future.result(timeout=60)

        raw = result.content[0].text
        return json.loads(raw)


def make_mcp_session(server_url: str) -> _MCPSession:
    """Create and return a persistent MCP session for the given server URL."""
    return _MCPSession(server_url)
