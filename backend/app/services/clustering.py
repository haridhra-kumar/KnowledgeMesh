import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import sqlite3

class FactClusterService:
    """
    Manages fact clustering incrementally.
    Groups facts that refer to the same underlying concept/metric into clusters.
    """

    @staticmethod
    def cluster_fact(conn: sqlite3.Connection, fact: Dict[str, Any]) -> str:
        """
        Incrementally assign a fact to an existing cluster or create a new cluster.
        Returns cluster_id.
        """
        fact_id = fact["id"]
        subject = fact.get("subject", "").strip()
        predicate = fact.get("predicate", "").strip()
        period = fact.get("period")
        scope = fact.get("scope")

        # Canonical keys (case-folded and normalized)
        canon_subj = subject.title()
        canon_pred = predicate.title()
        canon_period = period.upper() if period else None
        canon_scope = scope.lower() if scope else None

        # Build human-readable cluster display name
        parts = [canon_subj, canon_pred]
        if canon_period:
            parts.append(canon_period)
        if canon_scope:
            parts.append(f"({canon_scope})")
        display_name = " — ".join(parts)

        # Check if matching cluster already exists
        cursor = conn.cursor()
        query = """
            SELECT id, fact_count FROM fact_clusters
            WHERE LOWER(canonical_subject) = LOWER(?)
              AND LOWER(canonical_predicate) = LOWER(?)
              AND (canonical_period = ? OR (canonical_period IS NULL AND ? IS NULL))
              AND (canonical_scope = ? OR (canonical_scope IS NULL AND ? IS NULL))
            LIMIT 1
        """
        cursor.execute(query, (canon_subj, canon_pred, canon_period, canon_period, canon_scope, canon_scope))
        row = cursor.fetchone()

        now_str = datetime.now(timezone.utc).isoformat()

        if row:
            cluster_id = row[0]
            # Link member if not already linked
            cursor.execute("""
                INSERT OR IGNORE INTO cluster_members (cluster_id, fact_id, similarity_score, added_at)
                VALUES (?, ?, 1.0, ?)
            """, (cluster_id, fact_id, now_str))
        else:
            cluster_id = str(uuid.uuid4())
            description = f"Consolidated observations for {canon_subj} {canon_pred}"
            if canon_period:
                description += f" in {canon_period}"
            cursor.execute("""
                INSERT INTO fact_clusters (
                    id, canonical_subject, canonical_predicate, canonical_period,
                    canonical_scope, display_name, description, fact_count,
                    source_doc_count, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, 1, ?, ?)
            """, (cluster_id, canon_subj, canon_pred, canon_period, canon_scope, display_name, description, now_str, now_str))

            cursor.execute("""
                INSERT INTO cluster_members (cluster_id, fact_id, similarity_score, added_at)
                VALUES (?, ?, 1.0, ?)
            """, (cluster_id, fact_id, now_str))

        # Recompute fact_count and source_doc_count for the cluster
        cursor.execute("""
            SELECT COUNT(DISTINCT m.fact_id), COUNT(DISTINCT f.document_id)
            FROM cluster_members m
            JOIN facts f ON m.fact_id = f.id
            WHERE m.cluster_id = ?
        """, (cluster_id,))
        count_row = cursor.fetchone()
        if count_row:
            cursor.execute("""
                UPDATE fact_clusters
                SET fact_count = ?, source_doc_count = ?, updated_at = ?
                WHERE id = ?
            """, (count_row[0], count_row[1], now_str, cluster_id))

        return cluster_id
