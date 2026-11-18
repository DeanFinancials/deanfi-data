"""Phase 2 catalyst integration for the Market Pulse Input package.

Reads `daily-news/market_catalysts.json` (produced by deanfi-collectors),
applies a small macro/policy release calendar to decide whether
official-source coverage is required, and validates completeness:

- ranked-catalyst count must meet ``metadata.expected_min_catalysts``
- on macro-release days, at least one ranked catalyst must be ``source_tier == "official"``
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Iterable


# Phase 2 macro/policy release calendar (US, America/New_York).
# Keep deliberately small + auditable. Update annually (a validation warning
# fires within CALENDAR_EXPIRY_WARNING_DAYS of the last covered year's end).
#
# Covers: FOMC decision days, BLS Employment Situation (NFP), BLS CPI, BLS
# PPI, BEA GDP, and BEA Personal Income & Outlays (PCE) — the six release
# kinds the Phase 2 runbook commits to enforcing official-source coverage
# for.
#
# Sources (fetched 2026-11-18):
# - FOMC: https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm
#   (page last updated 2026-11-12). The 2027 dates are TENTATIVE: the Fed
#   confirms each one at the preceding meeting, so re-check them during 2027.
# - BLS: https://www.bls.gov/schedule/2026/home.htm,
#   https://www.bls.gov/schedule/2027/home.htm and
#   https://www.bls.gov/schedule/news_release/{empsit,cpi,ppi}.htm
# - BEA: https://www.bea.gov/news/schedule/full (2026) and
#   https://www.bea.gov/news/schedule/next-year (2027, modified 2026-11-18).
#   GDP and Personal Income & Outlays (PCE) are released on the same day.
#   2026-01-22 is the updated Q3 2025 GDP estimate.
_RELEASE_DATES_BY_YEAR: dict[str, dict[str, tuple[str, ...]]] = {
    "2026": {
        # FOMC decision days (statement at 2pm ET).
        "FOMC": ("01-28", "03-18", "04-29", "06-17", "07-29", "09-16", "10-28", "12-09"),
        "NFP": ("01-09", "02-11", "03-06", "04-03", "05-08", "06-05", "07-02", "08-07",
                "09-04", "10-02", "11-06", "12-04"),
        "CPI": ("01-13", "02-13", "03-11", "04-10", "05-12", "06-10", "07-14", "08-12",
                "09-11", "10-14", "11-10", "12-10"),
        "PPI": ("01-14", "01-30", "02-27", "03-18", "04-14", "05-13", "06-11", "07-15",
                "08-13", "09-10", "10-15", "11-13", "12-15"),
        "GDP": ("01-22", "02-20", "03-13", "04-09", "04-30", "05-28", "06-25", "07-30",
                "08-26", "09-30", "10-29", "11-25", "12-23"),
        "PCE": ("01-22", "02-20", "03-13", "04-09", "04-30", "05-28", "06-25", "07-30",
                "08-26", "09-30", "10-29", "11-25", "12-23"),
    },
    "2027": {
        # FOMC 2027 dates are tentative until confirmed at the preceding meeting.
        "FOMC": ("01-27", "03-17", "04-28", "06-09", "07-28", "09-15", "10-27", "11-17"),
        "NFP": ("01-08", "02-05", "03-05", "04-02", "05-07", "06-04", "07-02", "08-06",
                "09-03", "10-08", "11-05", "12-03"),
        "CPI": ("01-13", "02-11", "03-10", "04-13", "05-12", "06-10", "07-14", "08-11",
                "09-14", "10-14", "11-10", "12-10"),
        "PPI": ("01-14", "02-12", "03-12", "04-14", "05-13", "06-11", "07-15", "08-10",
                "09-10", "10-15", "11-12", "12-15"),
        "GDP": ("01-28", "02-25", "03-31", "04-29", "05-27", "06-25", "07-29", "08-25",
                "09-30", "10-28", "11-24", "12-22"),
        "PCE": ("01-28", "02-25", "03-31", "04-29", "05-27", "06-25", "07-29", "08-25",
                "09-30", "10-28", "11-24", "12-22"),
    },
}

MACRO_RELEASE_CALENDAR: tuple[dict, ...] = tuple(
    {"date": f"{year}-{month_day}", "kind": kind}
    for year, kinds in _RELEASE_DATES_BY_YEAR.items()
    for kind, dates in kinds.items()
    for month_day in dates
)

# Backward-compatible name for callers/tests that predate the multi-year calendar.
MACRO_RELEASE_CALENDAR_2026: tuple[dict, ...] = tuple(
    entry for entry in MACRO_RELEASE_CALENDAR if entry["date"].startswith("2026-")
)

_RELEASE_DATES = {entry["date"] for entry in MACRO_RELEASE_CALENDAR}
_CALENDAR_YEARS = {entry["date"][:4] for entry in MACRO_RELEASE_CALENDAR}

# Warn (non-blocking) this many days before the calendar's last covered year ends.
CALENDAR_EXPIRY_WARNING_DAYS = 60


def calendar_expiry_warning(market_date: str | None) -> str | None:
    """Return a non-blocking warning when the calendar is about to run out.

    Fires when ``market_date`` is within :data:`CALENDAR_EXPIRY_WARNING_DAYS`
    of 31 December of the last covered year. Dates in uncovered years are
    handled by the blocking :class:`CalendarYearMissing` path instead.
    """
    if not market_date:
        return None
    try:
        current = date.fromisoformat(market_date[:10])
    except ValueError:
        return None
    last_year = max(int(year) for year in _CALENDAR_YEARS)
    if current.year > last_year:
        return None
    calendar_end = date(last_year, 12, 31)
    if (calendar_end - current).days <= CALENDAR_EXPIRY_WARNING_DAYS:
        return (
            f"macro release calendar ends {calendar_end.isoformat()}; "
            f"add {last_year + 1} dates to dailycombined/catalyst_integration.py"
        )
    return None


class CalendarYearMissing(Exception):
    """Raised when the macro release calendar does not cover the market year."""


def is_release_day(market_date: str | None) -> bool:
    """Return True iff ``market_date`` matches a Phase 2 macro/policy release day.

    Raises :class:`CalendarYearMissing` when ``market_date`` falls in a year
    the calendar does not cover, so a stale calendar produces a loud,
    publish-blocking failure instead of silently returning False (which would
    let articles publish on real release days without official-source
    coverage). Add each new year to :data:`_RELEASE_DATES_BY_YEAR` annually.
    """
    if not market_date:
        return False
    year = market_date[:4]
    if year not in _CALENDAR_YEARS:
        raise CalendarYearMissing(
            f"macro release calendar covers {sorted(_CALENDAR_YEARS)}; "
            f"market_date {market_date!r} is outside that range — add "
            f"{year} release dates to _RELEASE_DATES_BY_YEAR."
        )
    return market_date in _RELEASE_DATES


class CatalystLoadError(Exception):
    """Raised when ``market_catalysts.json`` exists but cannot be parsed.

    A missing file is *not* an error (Phase 2 not yet deployed); a corrupted
    or partially-written file *is*, because treating it as "no Phase 2 yet"
    silently bypasses the publish gate.
    """


def load_market_catalysts(data_dir: Path) -> dict | None:
    """Load ``daily-news/market_catalysts.json`` if present.

    Returns ``None`` when the file does not exist. Raises
    :class:`CatalystLoadError` when the file exists but is unreadable or
    malformed — that case must not be confused with "Phase 2 not deployed".
    """
    path = Path(data_dir) / "daily-news" / "market_catalysts.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        raise CatalystLoadError(f"{path}: {exc}") from exc


def validate_completeness(payload: dict, *, market_date: str | None) -> dict:
    """Validate catalyst completeness against publish rules.

    Rules:
    - ranked count must be ``>= metadata.expected_min_catalysts``
    - on macro/policy release days, at least one ranked catalyst must be ``source_tier == "official"``
    """
    metadata = payload.get("metadata") or {}
    ranked = payload.get("ranked") or []
    expected_min = int(metadata.get("expected_min_catalysts") or 3)

    errors: list[str] = []
    if len(ranked) < expected_min:
        errors.append(
            f"catalysts.ranked too small: got {len(ranked)}, expected at least {expected_min}"
        )

    try:
        release_day = is_release_day(market_date)
    except CalendarYearMissing as exc:
        # Stale calendar -> blocking failure rather than silent "not a release day".
        errors.append(f"macro release calendar stale: {exc}")
        release_day = False

    if release_day:
        has_official = any((c.get("source_tier") == "official") for c in ranked)
        if not has_official:
            errors.append(
                "catalysts.ranked missing official source on macro/policy release day"
            )

    return {"is_valid": not errors, "errors": errors}


def _sector_matches(sector: str, *, title: str, related_symbols: Iterable[str]) -> bool:
    """Return True iff ``sector`` matches the catalyst's title or symbols.

    Uses word-boundary regex against the title and exact (case-insensitive)
    membership against ``related_symbols``. ``why_it_matters`` boilerplate
    is intentionally excluded — it expands the false-positive surface (e.g.
    "Energy" matching "synergy"/"renewable energy boilerplate") without
    adding signal.
    """
    sector_norm = sector.strip()
    if not sector_norm:
        return False
    # \b doesn't handle sectors with internal punctuation (e.g. "Real Estate"
    # is fine, but "Comm. Services" needs us to treat the dot as literal).
    pattern = r'\b' + re.escape(sector_norm) + r'\b'
    if re.search(pattern, title or '', flags=re.IGNORECASE):
        return True
    target = sector_norm.lower()
    return any((sym or '').strip().lower() == target for sym in related_symbols)


def apply_market_context(
    payload: dict,
    *,
    sector_leaders: Iterable[dict] | None = None,
    sector_laggards: Iterable[dict] | None = None,
    boost_per_match: float = 12.0,
) -> dict:
    """Re-score catalysts using same-day market-move context.

    Adds ``boost_per_match`` points (default 12) to ``relevance_score`` for
    every today's-leader/laggard sector name the catalyst's title or
    ``related_symbols`` mentions (word-boundary match, case-insensitive),
    and records the matched sector under ``related_data_points``. Re-sorts
    the ranked list by the new score.

    Idempotent: a second call short-circuits via
    ``metadata.market_context_applied`` so a later AI re-rank pass cannot
    double-boost scores.
    """
    existing_meta = payload.get('metadata') or {}
    if existing_meta.get('market_context_applied'):
        return payload

    sectors: list[str] = []
    for entry in list(sector_leaders or []) + list(sector_laggards or []):
        name = (entry.get('sector') or '').strip()
        if name:
            sectors.append(name)
    sectors = list(dict.fromkeys(sectors))  # preserve order, dedupe

    ranked = []
    for catalyst in payload.get('ranked', []):
        c = dict(catalyst)
        title = c.get('title') or ''
        related_symbols = c.get('related_symbols') or []
        matched = [s for s in sectors if _sector_matches(s, title=title, related_symbols=related_symbols)]
        if matched:
            existing = list(c.get('related_data_points') or [])
            for s in matched:
                if s not in existing:
                    existing.append(s)
            c['related_data_points'] = existing
            c['relevance_score'] = round(float(c.get('relevance_score') or 0.0) + boost_per_match * len(matched), 4)
        ranked.append(c)
    ranked.sort(key=lambda c: c.get('relevance_score') or 0.0, reverse=True)

    out = dict(payload)
    out['ranked'] = ranked
    new_meta = dict(existing_meta)
    new_meta['market_context_applied'] = True
    out['metadata'] = new_meta
    return out


def required_official_release_today(market_date: str | None) -> dict:
    """Lightweight summary for embedding in `market_pulse_input.json`.

    Returns a flat shape with separate boolean + list keys so downstream
    truthy checks like ``if catalysts.official_release_today:`` work as
    written. (The previous ``{"required": bool, "kinds": [str]}`` dict was
    always truthy because non-empty dicts are truthy even when ``required``
    is False.)
    """
    try:
        on_release_day = is_release_day(market_date)
    except CalendarYearMissing:
        # Calendar stale -- callers also see the blocking failure surfaced by
        # validate_completeness; here we conservatively report "no release".
        return {"official_release_today": False, "official_release_kinds": []}
    if not on_release_day:
        return {"official_release_today": False, "official_release_kinds": []}
    kinds = sorted({entry["kind"] for entry in MACRO_RELEASE_CALENDAR if entry["date"] == market_date})
    return {"official_release_today": True, "official_release_kinds": kinds}
