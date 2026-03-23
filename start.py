import subprocess
import threading
import sys
import os
import time

BASE = os.path.dirname(os.path.abspath(__file__))
FRONTEND = os.path.join(BASE, "frontend")
NODE = r"C:\Program Files\nodejs\npm.cmd"

# Ensure Node.js is on PATH for subprocesses
node_env = os.environ.copy()
node_env["PATH"] = r"C:\Program Files\nodejs" + os.pathsep + node_env.get("PATH", "")

def stream(proc, label):
    for line in iter(proc.stdout.readline, b""):
        print(f"[{label}] {line.decode(errors='replace').rstrip()}", flush=True)

def main():
    # ── Step 1: Build the static frontend (blocking — must finish first) ────────
    print("Building Next.js frontend...")
    result = subprocess.run(
        [NODE, "run", "build"],
        cwd=FRONTEND,
        env=node_env,
    )
    if result.returncode != 0:
        print("Frontend build failed — aborting.")
        sys.exit(1)
    print("Frontend built.\n")

    # ── Step 2: Start MCP server ────────────────────────────────────────────────
    print("Starting MCP server on http://127.0.0.1:5002 ...")
    mcp_srv = subprocess.Popen(
        [sys.executable, os.path.join(BASE, "mcp_server", "server.py")],
        cwd=BASE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    threading.Thread(target=stream, args=(mcp_srv, "MCP    "), daemon=True).start()

    time.sleep(5)  # wait for MCP server to be ready before Flask connects

    # ── Step 3: Start Flask (serves API + static frontend) ─────────────────────
    print("Starting Flask on http://localhost:5000 ...")
    flask = subprocess.Popen(
        [sys.executable, "app.py"],
        cwd=BASE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    threading.Thread(target=stream, args=(flask, "Flask  "), daemon=True).start()

    print("\nAll servers running.")
    print("  MCP Server:   http://127.0.0.1:5002")
    print("  App:          http://localhost:5000   <- open this")
    print("  Press Ctrl+C to stop all.\n")

    try:
        mcp_srv.wait()
        flask.wait()
    except KeyboardInterrupt:
        print("\nStopping...")
        mcp_srv.terminate()
        flask.terminate()

if __name__ == "__main__":
    main()
