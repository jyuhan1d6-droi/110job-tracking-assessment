from datetime import datetime
from zoneinfo import ZoneInfo


def normalize_deadline(source_code: str, deadline_raw: str | None) -> datetime | None:
    """Convert an explicitly supplied source deadline into its structured value."""
    if deadline_raw is None:
        return None
    if source_code == "shixiseng":
        try:
            return datetime.strptime(deadline_raw, "%Y-%m-%d").replace(
                hour=23, minute=59, second=59, tzinfo=ZoneInfo("Asia/Shanghai")
            )
        except ValueError:
            return None
    return None
