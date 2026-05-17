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
from pathlib import Path
from typing import Iterable


# Phase 2 macro/policy release calendar (US, America/New_York).
# Keep deliberately small + auditable. Sources: FOMC schedule, BLS / BEA
# release calendars. Update annually.
#
# Covers: FOMC decision days, BLS Employment Situation (NFP), BLS CPI, BLS
# PPI, BEA GDP, and BEA Personal Income & Outlays (PCE) — the six release
# kinds the Phase 2 runbook commits to enforcing official-source coverage
# for. Schedule based on BLS / BEA published 2026 release calendars.
MACRO_RELEASE_CALENDAR_2026: tuple[dict, ...] = (
    # FOMC meeting decision days (statement at 2pm ET).
    {"date": "2026-01-28", "kind": "FOMC"},
    {"date": "2026-03-18", "kind": "FOMC"},
    {"date": "2026-04-29", "kind": "FOMC"},
    {"date": "2026-06-17", "kind": "FOMC"},
    {"date": "2026-07-29", "kind": "FOMC"},
    {"date": "2026-09-16", "kind": "FOMC"},
    {"date": "2026-10-28", "kind": "FOMC"},
    {"date": "2026-12-09", "kind": "FOMC"},
    # BLS Employment Situation (first-Friday cadence).
    {"date": "2026-01-09", "kind": "NFP"},
    {"date": "2026-02-06", "kind": "NFP"},
    {"date": "2026-03-06", "kind": "NFP"},
    {"date": "2026-04-03", "kind": "NFP"},
    {"date": "2026-05-08", "kind": "NFP"},
    {"date": "2026-06-05", "kind": "NFP"},
    {"date": "2026-07-02", "kind": "NFP"},
    {"date": "2026-08-07", "kind": "NFP"},
    {"date": "2026-09-04", "kind": "NFP"},
    {"date": "2026-10-02", "kind": "NFP"},
    {"date": "2026-11-06", "kind": "NFP"},
    {"date": "2026-12-04", "kind": "NFP"},
    # BLS CPI (mid-month).
    {"date": "2026-01-13", "kind": "CPI"},
    {"date": "2026-02-11", "kind": "CPI"},
    {"date": "2026-03-12", "kind": "CPI"},
    {"date": "2026-04-14", "kind": "CPI"},
    {"date": "2026-05-13", "kind": "CPI"},
    {"date": "2026-06-10", "kind": "CPI"},
    {"date": "2026-07-15", "kind": "CPI"},
    {"date": "2026-08-12", "kind": "CPI"},
    {"date": "2026-09-10", "kind": "CPI"},
    {"date": "2026-10-15", "kind": "CPI"},
    {"date": "2026-11-13", "kind": "CPI"},
    {"date": "2026-12-10", "kind": "CPI"},
    # BLS PPI (typically one business day after CPI).
    {"date": "2026-01-14", "kind": "PPI"},
    {"date": "2026-02-12", "kind": "PPI"},
    {"date": "2026-03-13", "kind": "PPI"},
    {"date": "2026-04-15", "kind": "PPI"},
    {"date": "2026-05-14", "kind": "PPI"},
    {"date": "2026-06-11", "kind": "PPI"},
    {"date": "2026-07-16", "kind": "PPI"},
    {"date": "2026-08-13", "kind": "PPI"},
    {"date": "2026-09-11", "kind": "PPI"},
    {"date": "2026-10-16", "kind": "PPI"},
    {"date": "2026-11-16", "kind": "PPI"},
    {"date": "2026-12-11", "kind": "PPI"},
    # BEA GDP (advance/second/third estimates, monthly cadence).
    {"date": "2026-01-29", "kind": "GDP"},
    {"date": "2026-02-26", "kind": "GDP"},
    {"date": "2026-03-26", "kind": "GDP"},
    {"date": "2026-04-29", "kind": "GDP"},
    {"date": "2026-05-28", "kind": "GDP"},
    {"date": "2026-06-25", "kind": "GDP"},
    {"date": "2026-07-30", "kind": "GDP"},
    {"date": "2026-08-27", "kind": "GDP"},
    {"date": "2026-09-24", "kind": "GDP"},
    {"date": "2026-10-29", "kind": "GDP"},
    {"date": "2026-11-25", "kind": "GDP"},
    {"date": "2026-12-22", "kind": "GDP"},
    # BEA Personal Income & Outlays / PCE.
    {"date": "2026-01-30", "kind": "PCE"},
    {"date": "2026-02-27", "kind": "PCE"},
    {"date": "2026-03-27", "kind": "PCE"},
    {"date": "2026-04-30", "kind": "PCE"},
    {"date": "2026-05-29", "kind": "PCE"},
    {"date": "2026-06-26", "kind": "PCE"},
    {"date": "2026-07-31", "kind": "PCE"},
    {"date": "2026-08-28", "kind": "PCE"},
    {"date": "2026-09-25", "kind": "PCE"},
    {"date": "2026-10-30", "kind": "PCE"},
    {"date": "2026-11-25", "kind": "PCE"},
    {"date": "2026-12-23", "kind": "PCE"},
)

_RELEASE_DATES = {entry["date"] for entry in MACRO_RELEASE_CALENDAR_2026}
_CALENDAR_YEARS = {entry["date"][:4] for entry in MACRO_RELEASE_CALENDAR_2026}


class CalendarYearMissing(Exception):
    """Raised when the macro release calendar does not cover the market year."""


def is_release_day(market_date: str | None) -> bool:
    """Return True iff ``market_date`` matches a Phase 2 macro/policy release day.

    Raises :class:`CalendarYearMissing` when ``market_date`` falls in a year
    the calendar does not cover, so a stale calendar produces a loud,
    publish-blocking failure instead of silently returning False (which would
    let articles publish on real release days without official-source
    coverage). Update :data:`MACRO_RELEASE_CALENDAR_2026` annually.
    """
    if not market_date:
        return False
    year = market_date[:4]
    if year not in _CALENDAR_YEARS:
        raise CalendarYearMissing(
            f"macro release calendar covers {sorted(_CALENDAR_YEARS)}; "
            f"market_date {market_date!r} is outside that range — update "
            f"MACRO_RELEASE_CALENDAR_{year}."
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
    kinds = sorted({entry["kind"] for entry in MACRO_RELEASE_CALENDAR_2026 if entry["date"] == market_date})
    return {"official_release_today": True, "official_release_kinds": kinds}
