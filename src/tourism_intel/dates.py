"""Period parsing. Unparseable values raise, they are never guessed."""

from __future__ import annotations

import re
from datetime import date, datetime

import pandas as pd

_MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


def parse_month(value) -> pd.Timestamp:
    """Return the first day of the month for a value like '2024-03', 'Mar 2024', 'March-2024',
    '2024-03-15', a date or a datetime."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        raise ValueError("missing period")
    if isinstance(value, pd.Timestamp | datetime | date):
        ts = pd.Timestamp(value)
        return pd.Timestamp(ts.year, ts.month, 1)
    s = str(value).strip()
    m = re.fullmatch(r"(\d{4})[-/](\d{1,2})(?:[-/]\d{1,2})?", s)
    if m:
        y, mo = int(m[1]), int(m[2])
    else:
        m = re.fullmatch(r"([A-Za-z]+)[\s\-/,]*(\d{4})", s)
        if not m or m[1][:3].lower() not in _MONTHS:
            raise ValueError(f"unparseable period: {value!r}")
        y, mo = int(m[2]), _MONTHS[m[1][:3].lower()]
    if not 1 <= mo <= 12 or not 1900 <= y <= 2100:
        raise ValueError(f"invalid period: {value!r}")
    return pd.Timestamp(y, mo, 1)
