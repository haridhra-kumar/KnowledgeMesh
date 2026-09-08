import sqlite3
import json
from pathlib import Path
from typing import Generator, Any, Dict, List, Optional
from contextlib import contextmanager

from app.config import settings

def get_db_connection() -> sqlite3.Connection:
    """Create a new SQLite connection with WAL mode and row factory."""
    settings.ensure_directories()
    conn = sqlite3.connect(
        settings.database_path,
        timeout=30.0,
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    return conn

@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for SQLite database connections."""
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db() -> None:
    """Initialize database tables using schema.sql."""
    schema_path = Path(__file__).parent / "models" / "schema.sql"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found at {schema_path}")

    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    with get_db() as conn:
        conn.executescript(schema_sql)

def row_to_dict(row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
    """Convert sqlite3.Row to dictionary with parsed JSON fields where appropriate."""
    if row is None:
        return None
    d = dict(row)
    for json_key in ["qualifiers_json", "comparison_context_json", "metadata_json", "logs_json"]:
        if json_key in d and d[json_key]:
            try:
                d[json_key] = json.loads(d[json_key])
            except Exception:
                pass
    return d

def rows_to_dicts(rows: List[sqlite3.Row]) -> List[Dict[str, Any]]:
    """Convert a list of sqlite3.Row to dictionaries."""
    return [row_to_dict(r) for r in rows if r is not None]
