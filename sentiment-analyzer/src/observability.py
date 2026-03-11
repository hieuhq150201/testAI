"""
📊 Agent-QA2: Observability — SQLite prediction logger + stats
"""
import sqlite3, os, time, hashlib, threading
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '../data/predictions.db')
_lock = threading.Lock()

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text_hash TEXT NOT NULL,
                text_preview TEXT,
                sentiment TEXT NOT NULL,
                confidence REAL NOT NULL,
                pos_prob REAL,
                neg_prob REAL,
                source TEXT DEFAULT "api",
                latency_ms REAL,
                created_at TEXT
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_created ON predictions(created_at)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_sentiment ON predictions(sentiment)')
        conn.commit()

def log_prediction(text: str, result: dict, source="api", latency_ms=None):
    with _lock:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute('''
                INSERT INTO predictions (text_hash, text_preview, sentiment, confidence, pos_prob, neg_prob, source, latency_ms, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime("now"))
            ''', (
                hashlib.md5(text.encode()).hexdigest(),
                text[:100],
                result.get("sentiment"),
                result.get("confidence"),
                result.get("positive_prob", result.get("pos_prob")),
                result.get("negative_prob", result.get("neg_prob")),
                source,
                latency_ms
            ))
            conn.commit()

def get_stats():
    with sqlite3.connect(DB_PATH) as conn:
        total = conn.execute('SELECT COUNT(*) FROM predictions').fetchone()[0]
        if total == 0:
            return {"total": 0, "message": "No predictions yet"}

        pos = conn.execute("SELECT COUNT(*) FROM predictions WHERE sentiment='positive'").fetchone()[0]
        neg = total - pos
        avg_conf = conn.execute('SELECT AVG(confidence) FROM predictions').fetchone()[0]
        avg_lat  = conn.execute('SELECT AVG(latency_ms) FROM predictions WHERE latency_ms IS NOT NULL').fetchone()[0]
        uncertain = conn.execute("SELECT COUNT(*) FROM predictions WHERE confidence < 0.6").fetchone()[0]
        recent = conn.execute('''
            SELECT sentiment, confidence, text_preview, created_at
            FROM predictions ORDER BY id DESC LIMIT 5
        ''').fetchall()
        hourly = conn.execute('''
            SELECT strftime('%Y-%m-%d %H:00', created_at) as hour, COUNT(*) as count
            FROM predictions GROUP BY hour ORDER BY hour DESC LIMIT 24
        ''').fetchall()

    return {
        "total": total,
        "positive": pos,
        "negative": neg,
        "positive_rate": round(pos/total, 4),
        "avg_confidence": round(avg_conf or 0, 4),
        "avg_latency_ms": round(avg_lat or 0, 2),
        "uncertain_count": uncertain,
        "uncertain_rate": round(uncertain/total, 4),
        "recent_predictions": [
            {"sentiment": r[0], "confidence": r[1], "preview": r[2], "at": r[3]}
            for r in recent
        ],
        "hourly_volume": [{"hour": r[0], "count": r[1]} for r in hourly]
    }

init_db()


# ── User Feedback ─────────────────────────────────────────────────
def _init_feedback_table():
    with _lock:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT,
                predicted TEXT,
                correct INTEGER,
                user_label TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
            conn.commit()

def log_feedback(text: str, predicted: str, correct: bool, user_label: str = None):
    _init_feedback_table()
    with _lock:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "INSERT INTO feedback(text, predicted, correct, user_label) VALUES(?,?,?,?)",
                (text, predicted, 1 if correct else 0, user_label)
            )
            conn.commit()

def get_feedback_stats() -> dict:
    _init_feedback_table()
    with _lock:
        with sqlite3.connect(DB_PATH) as conn:
            total = conn.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
            correct = conn.execute("SELECT COUNT(*) FROM feedback WHERE correct=1").fetchone()[0]
    return {
        "total": total,
        "correct": correct,
        "accuracy": round(correct / total, 4) if total else None,
    }
