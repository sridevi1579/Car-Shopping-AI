import sqlite3, json, sys

if len(sys.argv) < 2:
    print("Usage: python read_session.py <session_id>")
    print("Example: python read_session.py tradein:e6ac3e6f-04d0-4372-9865-7edae84c5c1f")
    sys.exit(1)

sid = sys.argv[1]
with sqlite3.connect('data/sessions.db') as conn:
    row = conn.execute('SELECT history FROM sessions WHERE id = ?', (sid,)).fetchone()

if not row:
    print("Session not found or expired.")
    sys.exit(1)

history = json.loads(row[0])
print(f"=== {sid} — {len(history)} messages ===\n")
for msg in history:
    role = msg['role'].upper()
    content = msg['content']
    if isinstance(content, list):
        content = ' '.join(
            b.get('text', '') for b in content if isinstance(b, dict) and b.get('type') == 'text'
        )
    print(f"[{role}]\n{content}\n")
