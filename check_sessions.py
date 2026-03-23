import sqlite3, time

db = 'data/sessions.db'
with sqlite3.connect(db) as conn:
    rows = conn.execute(
        'SELECT id, updated_at, length(history) FROM sessions ORDER BY updated_at DESC'
    ).fetchall()

if not rows:
    print("No sessions found.")
else:
    print(f"{'Session ID':<40} {'Age (min)':<12} {'Size (bytes)'}")
    print('-' * 65)
    for sid, ts, size in rows:
        age = (time.time() - ts) / 60
        print(f"{sid:<40} {age:<12.1f} {size}")
