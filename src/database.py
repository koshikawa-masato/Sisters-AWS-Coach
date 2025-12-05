"""
Database module for Sisters-AWS-Coach v2
SQLite implementation for user progress and weakness analysis
"""

import sqlite3
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager


# Database path
DB_PATH = Path(__file__).parent.parent / "data" / "aws_coach.db"


def get_db_path() -> Path:
    """Get database path, create directory if needed"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return DB_PATH


@contextmanager
def get_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database():
    """Initialize database tables"""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                display_name TEXT,
                preferred_language TEXT DEFAULT 'ja',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Answer history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS answer_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                question_hash TEXT,
                character TEXT NOT NULL,
                tags TEXT NOT NULL,
                is_correct BOOLEAN NOT NULL,
                answer_time_sec REAL,
                language TEXT DEFAULT 'ja',
                mode TEXT DEFAULT 'online',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Weakness summary table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weakness_summary (
                user_id TEXT NOT NULL,
                tag TEXT NOT NULL,
                total_count INTEGER DEFAULT 0,
                correct_count INTEGER DEFAULT 0,
                accuracy_rate REAL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, tag),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                character TEXT NOT NULL,
                mode TEXT DEFAULT 'online',
                question_count INTEGER DEFAULT 0,
                correct_count INTEGER DEFAULT 0,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ended_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Create indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_answer_history_user
            ON answer_history(user_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_answer_history_tags
            ON answer_history(tags)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_weakness_user
            ON weakness_summary(user_id)
        """)


def get_or_create_user(user_id: str, display_name: Optional[str] = None) -> Dict:
    """Get existing user or create new one"""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Check if user exists
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()

        if row:
            return dict(row)

        # Create new user
        cursor.execute(
            "INSERT INTO users (id, display_name) VALUES (?, ?)",
            (user_id, display_name or f"User_{user_id[:8]}")
        )

        return {
            "id": user_id,
            "display_name": display_name or f"User_{user_id[:8]}",
            "preferred_language": "ja",
            "created_at": datetime.now().isoformat()
        }


def record_answer(
    user_id: str,
    character: str,
    tags: List[str],
    is_correct: bool,
    question_text: str = "",
    answer_time_sec: Optional[float] = None,
    language: str = "ja",
    mode: str = "online"
) -> int:
    """Record an answer in history and update weakness summary"""

    # Generate question hash for deduplication
    question_hash = hashlib.md5(question_text.encode()).hexdigest()[:16] if question_text else None

    with get_connection() as conn:
        cursor = conn.cursor()

        # Ensure user exists
        get_or_create_user(user_id)

        # Insert answer history
        cursor.execute("""
            INSERT INTO answer_history
            (user_id, question_hash, character, tags, is_correct, answer_time_sec, language, mode)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            question_hash,
            character,
            json.dumps(tags),
            is_correct,
            answer_time_sec,
            language,
            mode
        ))

        answer_id = cursor.lastrowid

        # Update weakness summary for each tag
        for tag in tags:
            cursor.execute("""
                INSERT INTO weakness_summary (user_id, tag, total_count, correct_count, accuracy_rate)
                VALUES (?, ?, 1, ?, ?)
                ON CONFLICT(user_id, tag) DO UPDATE SET
                    total_count = total_count + 1,
                    correct_count = correct_count + ?,
                    accuracy_rate = CAST(correct_count + ? AS REAL) / (total_count + 1),
                    last_updated = CURRENT_TIMESTAMP
            """, (
                user_id,
                tag,
                1 if is_correct else 0,
                1.0 if is_correct else 0.0,
                1 if is_correct else 0,
                1 if is_correct else 0
            ))

        return answer_id


def get_weaknesses(user_id: str, threshold: float = 0.6, limit: int = 5) -> List[Dict]:
    """Get user's weak areas (accuracy < threshold)"""
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT tag, total_count, correct_count, accuracy_rate
            FROM weakness_summary
            WHERE user_id = ? AND total_count >= 3 AND accuracy_rate < ?
            ORDER BY accuracy_rate ASC, total_count DESC
            LIMIT ?
        """, (user_id, threshold, limit))

        return [dict(row) for row in cursor.fetchall()]


def get_strengths(user_id: str, threshold: float = 0.8, limit: int = 5) -> List[Dict]:
    """Get user's strong areas (accuracy >= threshold)"""
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT tag, total_count, correct_count, accuracy_rate
            FROM weakness_summary
            WHERE user_id = ? AND total_count >= 3 AND accuracy_rate >= ?
            ORDER BY accuracy_rate DESC, total_count DESC
            LIMIT ?
        """, (user_id, threshold, limit))

        return [dict(row) for row in cursor.fetchall()]


def get_user_stats(user_id: str) -> Dict:
    """Get overall statistics for a user"""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Overall stats
        cursor.execute("""
            SELECT
                COUNT(*) as total_questions,
                SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct_count,
                AVG(CASE WHEN is_correct THEN 1.0 ELSE 0.0 END) as overall_accuracy,
                AVG(answer_time_sec) as avg_answer_time
            FROM answer_history
            WHERE user_id = ?
        """, (user_id,))

        overall = dict(cursor.fetchone())

        # Stats by character
        cursor.execute("""
            SELECT
                character,
                COUNT(*) as questions,
                SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct,
                AVG(CASE WHEN is_correct THEN 1.0 ELSE 0.0 END) as accuracy
            FROM answer_history
            WHERE user_id = ?
            GROUP BY character
        """, (user_id,))

        by_character = {row['character']: dict(row) for row in cursor.fetchall()}

        # Recent activity (last 7 days)
        cursor.execute("""
            SELECT
                DATE(created_at) as date,
                COUNT(*) as questions
            FROM answer_history
            WHERE user_id = ? AND created_at >= DATE('now', '-7 days')
            GROUP BY DATE(created_at)
            ORDER BY date
        """, (user_id,))

        recent_activity = [dict(row) for row in cursor.fetchall()]

        return {
            "overall": overall,
            "by_character": by_character,
            "recent_activity": recent_activity,
            "weaknesses": get_weaknesses(user_id),
            "strengths": get_strengths(user_id)
        }


def get_answer_history(
    user_id: str,
    limit: int = 50,
    character: Optional[str] = None
) -> List[Dict]:
    """Get recent answer history"""
    with get_connection() as conn:
        cursor = conn.cursor()

        query = """
            SELECT id, question_hash, character, tags, is_correct,
                   answer_time_sec, language, mode, created_at
            FROM answer_history
            WHERE user_id = ?
        """
        params = [user_id]

        if character:
            query += " AND character = ?"
            params.append(character)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)

        results = []
        for row in cursor.fetchall():
            item = dict(row)
            item['tags'] = json.loads(item['tags'])
            results.append(item)

        return results


def get_suggested_tags(user_id: str, count: int = 3) -> List[str]:
    """Get suggested tags to focus on based on weakness analysis"""
    weaknesses = get_weaknesses(user_id, threshold=0.7, limit=count)

    if weaknesses:
        return [w['tag'] for w in weaknesses]

    # If no clear weaknesses, return categories with least practice
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT tag, total_count
            FROM weakness_summary
            WHERE user_id = ?
            ORDER BY total_count ASC
            LIMIT ?
        """, (user_id, count))

        return [row['tag'] for row in cursor.fetchall()]


# SAA Exam Categories
SAA_CATEGORIES = [
    # Compute
    "EC2", "Lambda", "ECS", "EKS", "Fargate", "Batch", "Lightsail",
    # Storage
    "S3", "EBS", "EFS", "FSx", "Storage Gateway", "Snow Family",
    # Database
    "RDS", "DynamoDB", "Aurora", "ElastiCache", "Redshift", "DocumentDB", "Neptune",
    # Networking
    "VPC", "Route53", "CloudFront", "API Gateway", "ELB", "Direct Connect", "VPN", "Transit Gateway",
    # Security
    "IAM", "KMS", "Secrets Manager", "WAF", "Shield", "Cognito", "GuardDuty", "Inspector", "Macie",
    # Management
    "CloudWatch", "CloudTrail", "Config", "Organizations", "Systems Manager", "Trusted Advisor",
    # Application Integration
    "SQS", "SNS", "Step Functions", "EventBridge", "AppSync",
    # Cost
    "Cost Explorer", "Budgets", "Savings Plans", "Reserved Instances",
]


def get_all_categories() -> List[str]:
    """Get all SAA exam categories"""
    return SAA_CATEGORIES.copy()


# Initialize database on module import
init_database()
