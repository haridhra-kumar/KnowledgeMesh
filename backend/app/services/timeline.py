import re
import sqlite3
from typing import List, Dict, Any, Optional

def period_to_sort_key(period_str: Optional[str]) -> str:
    """
    Converts temporal period string into a chronological sort key.
    Explicitly decoupled from document page order.
    Examples:
    - 'FY2023' -> '2023-04-FY'
    - 'Q1 FY2024' -> '2023-06-Q1'
    - 'Q2 FY2024' -> '2023-09-Q2'
    - 'Q3 FY2024' -> '2023-12-Q3'
    - 'Q4 FY2024' -> '2024-03-Q4'
    - 'FY2024' -> '2024-04-FY'
    - '2024-03-31' -> '2024-03-31'
    - 'CY2024' -> '2024-12-CY'
    """
    if not period_str:
        return "9999-99-99"

    text = period_str.strip().upper()

    # Exact ISO date: YYYY-MM-DD
    iso_match = re.match(r'(\d{4})-(\d{2})-(\d{2})', text)
    if iso_match:
        return text

    # Quarter + Fiscal Year: e.g. Q1 FY2024
    q_fy = re.search(r'Q([1-4])\s*FY(?:20)?(\d{2})', text)
    if q_fy:
        quarter = int(q_fy.group(1))
        fy_year = int("20" + q_fy.group(2) if len(q_fy.group(2)) == 2 else q_fy.group(2))
        # Indian fiscal year Q1 is Apr-Jun of previous calendar year (e.g. FY24 Q1 is Jun 2023)
        cal_year = fy_year - 1 if quarter < 4 else fy_year
        month_map = {1: "06", 2: "09", 3: "12", 4: "03"}
        return f"{cal_year}-{month_map[quarter]}-Q{quarter}"

    # Fiscal Year: e.g. FY2024, FY24
    fy = re.search(r'FY(?:20)?(\d{2})', text)
    if fy:
        fy_year = "20" + fy.group(1) if len(fy.group(1)) == 2 else fy.group(1)
        return f"{fy_year}-04-FY"

    # Calendar Year: e.g. CY2024 or just 2024
    yr = re.search(r'(?:CY)?(20\d{2})', text)
    if yr:
        return f"{yr.group(1)}-12-CY"

    return f"9998-{text[:10]}"

class TimelineService:
    """
    Builds chronological timeline streams based on explicit fact metadata.
    """

    @staticmethod
    def get_timeline(
        conn: sqlite3.Connection,
        subject: Optional[str] = None,
        predicate: Optional[str] = None,
        document_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        cursor = conn.cursor()

        query = """
            SELECT
                f.id, f.document_id, f.page_number, f.subject, f.predicate,
                f.value, f.normalized_value, f.normalized_unit, f.period,
                f.evidence_quote, f.grounding_status, f.confidence,
                d.filename as document_filename
            FROM facts f
            JOIN documents d ON f.document_id = d.id
            WHERE f.status = 'ACCEPTED' AND f.period IS NOT NULL AND TRIM(f.period) != ''
        """
        params: List[Any] = []

        if subject:
            query += " AND LOWER(f.subject) LIKE LOWER(?)"
            params.append(f"%{subject.strip()}%")
        if predicate:
            query += " AND LOWER(f.predicate) LIKE LOWER(?)"
            params.append(f"%{predicate.strip()}%")
        if document_id:
            query += " AND f.document_id = ?"
            params.append(document_id)

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()

        # Map and attach true temporal sort key
        items = []
        for r in rows:
            p = r["period"]
            sort_key = period_to_sort_key(p)
            items.append({
                "id": f"time_{r['id']}",
                "fact_id": r["id"],
                "subject": r["subject"],
                "predicate": r["predicate"],
                "value": r["value"],
                "normalized_value": r["normalized_value"],
                "normalized_unit": r["normalized_unit"],
                "period": p,
                "date_sort_key": sort_key,
                "evidence_quote": r["evidence_quote"],
                "document_id": r["document_id"],
                "document_filename": r["document_filename"],
                "page_number": r["page_number"],
                "grounding_status": r["grounding_status"],
                "confidence": r["confidence"]
            })

        # Sort strictly by date_sort_key
        items.sort(key=lambda x: x["date_sort_key"])

        # Group by Subject + Predicate
        groups_dict: Dict[str, Dict[str, Any]] = {}
        for item in items:
            grp_key = f"{item['subject'].title()} — {item['predicate'].title()}"
            if grp_key not in groups_dict:
                groups_dict[grp_key] = {
                    "subject": item["subject"].title(),
                    "predicate": item["predicate"].title(),
                    "items": []
                }
            groups_dict[grp_key]["items"].append(item)

        return list(groups_dict.values())
