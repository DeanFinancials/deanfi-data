"""Optional low-token AI Catalyst Ranker.

Re-orders the deterministic ``ranked`` list using a small OpenAI model. The
model is asked to return a strict JSON object with a single ``ranked_urls``
array drawn from the input URLs. Any URL the model invents is dropped, and
any catalyst the model omits is appended at the end so the publish-gate
count rule still holds.

If the call fails for any reason (no API key, network error, unparseable
response, missing key), this returns the input payload unchanged so the
deterministic order from `deanfi-collectors` continues to govern.
"""

from __future__ import annotations

import json
import os
from datetime import date
from typing import Optional, Protocol


SYSTEM_PROMPT = (
    "You rank catalyst candidates for a daily US stock-market recap. You "
    "receive the market date, a short summary of the session's moves, and a "
    "JSON list of already-collected candidates. Order the candidates by how "
    "directly they explain or move US markets on the market date. Rank "
    "highest: US economic data released on or just before the market date "
    "(retail sales, CPI, PPI, jobs, GDP, PCE), Federal Reserve policy and "
    "Treasury yields, oil/gold/dollar and other commodity or currency moves, "
    "major US company earnings or guidance, and session recaps that name the "
    "drivers of the index or sector moves in the summary. Rank lower: foreign "
    "politics, elections, legislatures, border or diplomatic news with no "
    "stated link to markets, energy prices, or US companies; personal-finance, "
    "opinion, or promotional pieces; and items published well before the "
    "market date. Return ONLY a JSON object of the form "
    "{\"ranked_urls\": [\"<url>\", ...]} where every URL is copied verbatim "
    "from the input. Do not invent URLs. Do not add prose. Include every "
    "candidate."
)

# Candidates published this many days before the market date are not worth
# spending model attention on. They are demoted below fresh items (never
# dropped), so the catalyst count and official-source rules are unaffected.
STALE_CANDIDATE_MAX_AGE_DAYS = 60


class RankerClient(Protocol):
    def rank(self, *, model: str, messages: list, response_format: dict) -> dict: ...


RANKER_RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "catalyst_ranker_response",
        "strict": True,
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["ranked_urls"],
            "properties": {
                "ranked_urls": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
        },
    },
}


def _published_date(catalyst: dict) -> Optional[date]:
    value = catalyst.get("published_at")
    if not isinstance(value, str) or len(value) < 10:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def is_stale_candidate(
    catalyst: dict,
    market_date: Optional[str],
    *,
    max_age_days: int = STALE_CANDIDATE_MAX_AGE_DAYS,
) -> bool:
    """True when ``catalyst`` was published more than ``max_age_days`` before ``market_date``.

    Undated catalysts and an unknown market date are never stale: this filter
    only removes items that are clearly old.
    """
    if not market_date:
        return False
    try:
        market = date.fromisoformat(str(market_date)[:10])
    except ValueError:
        return False
    published = _published_date(catalyst)
    if published is None:
        return False
    return (market - published).days > max_age_days


def demote_stale_catalysts(payload: dict, *, max_age_days: int = STALE_CANDIDATE_MAX_AGE_DAYS) -> dict:
    """Move clearly stale catalysts below fresh ones, keeping relative order.

    Nothing is dropped, so ``validate_completeness`` sees the same count and
    the same official-tier items. Records ``stale_demoted_count`` in metadata.
    """
    metadata = dict(payload.get("metadata") or {})
    market_date = metadata.get("market_date")
    ranked = list(payload.get("ranked") or [])
    fresh = [c for c in ranked if not is_stale_candidate(c, market_date, max_age_days=max_age_days)]
    stale = [c for c in ranked if is_stale_candidate(c, market_date, max_age_days=max_age_days)]
    out = dict(payload)
    out["ranked"] = fresh + stale
    metadata["stale_demoted_count"] = len(stale)
    out["metadata"] = metadata
    return out


def _build_messages(payload: dict, market_summary: str, candidates: Optional[list] = None) -> list:
    source = payload.get("ranked", []) if candidates is None else candidates
    minimal = [
        {
            "title": c.get("title"),
            "source": c.get("source"),
            "source_tier": c.get("source_tier"),
            "category": c.get("category"),
            "published_at": c.get("published_at"),
            "url": c.get("url"),
            "why_it_matters": c.get("why_it_matters"),
        }
        for c in source
    ]
    user_content = json.dumps({
        "market_date": (payload.get("metadata") or {}).get("market_date"),
        "market_summary": market_summary,
        "candidates": minimal,
    })
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


def with_ranker_outcome(payload: dict, outcome: dict) -> dict:
    """Return a shallow copy of ``payload`` with ``metadata.ranker_outcome`` set.

    The outcome is telemetry only (status, model, reason, counts); it is what
    the combine workflow summary reports, since a fallback is otherwise silent.
    """
    out = dict(payload)
    metadata = dict(payload.get("metadata") or {})
    metadata["ranker_outcome"] = outcome
    out["metadata"] = metadata
    return out


def ai_rerank(
    payload: dict,
    *,
    market_summary: str,
    model_id: str,
    client: RankerClient,
) -> dict:
    """Apply AI ranking to ``payload`` or return its existing order on failure.

    Clearly stale candidates are not sent to the model; they stay below the
    model-ordered fresh candidates. ``metadata.ranker_outcome`` records what
    happened on every path.
    """
    market_date = (payload.get("metadata") or {}).get("market_date")
    by_url = {c.get("url"): c for c in payload.get("ranked", []) if c.get("url")}
    if not by_url:
        return with_ranker_outcome(payload, {"status": "skipped", "model": model_id, "reason": "no catalysts with URLs"})

    candidates = [c for c in by_url.values() if not is_stale_candidate(c, market_date)]
    stale = [c for c in by_url.values() if is_stale_candidate(c, market_date)]
    outcome = {
        "status": "fallback",
        "model": model_id,
        "reason": None,
        "candidates_sent": len(candidates),
        "stale_excluded": len(stale),
    }
    if not candidates:
        outcome.update(status="skipped", reason="every candidate is stale")
        return with_ranker_outcome(payload, outcome)

    messages = _build_messages(payload, market_summary, candidates)
    try:
        raw = client.rank(
            model=model_id,
            messages=messages,
            response_format=RANKER_RESPONSE_FORMAT,
        )
    except Exception as exc:
        outcome["reason"] = f"model call failed: {type(exc).__name__}: {exc}"[:300]
        return with_ranker_outcome(payload, outcome)

    if not isinstance(raw, dict) or not isinstance(raw.get("ranked_urls"), list):
        outcome["reason"] = "response missing ranked_urls list"
        return with_ranker_outcome(payload, outcome)
    ordered_urls = raw["ranked_urls"]

    candidate_urls = {c.get("url") for c in candidates}
    seen: set[str] = set()
    new_ranked = []
    for url in ordered_urls:
        if not isinstance(url, str):
            continue
        if url in seen or url not in candidate_urls:
            continue
        seen.add(url)
        new_ranked.append(by_url[url])

    # If no AI-supplied URL survived validation, the order is identical to
    # the deterministic input; don't relabel it as "ai" — that would be
    # misleading for downstream telemetry.
    if not seen:
        outcome["reason"] = "no returned URL matched an input candidate"
        return with_ranker_outcome(payload, outcome)

    # Append any fresh catalyst the model omitted, then the stale ones, so
    # completeness rules still hold.
    for catalyst in candidates:
        if catalyst.get("url") not in seen:
            new_ranked.append(catalyst)
    new_ranked.extend(stale)

    out = dict(payload)
    out["ranked"] = new_ranked
    metadata = dict(payload.get("metadata") or {})
    metadata["previous_ranking_method"] = metadata.get("ranking_method", "deterministic")
    metadata["ranking_method"] = "ai"
    metadata["ranker_model"] = model_id
    out["metadata"] = metadata
    outcome.update(status="ai", ranked_by_model=len(seen), omitted_by_model=len(candidates) - len(seen))
    return with_ranker_outcome(out, outcome)


class OpenAIRankerClient:  # pragma: no cover - thin runtime wrapper
    """Adapter for the OpenAI Python SDK's chat.completions.create."""

    def __init__(self, openai_client):
        self._client = openai_client

    def rank(self, *, model: str, messages: list, response_format: dict) -> dict:
        completion = self._client.chat.completions.create(
            model=model,
            messages=messages,
            response_format=response_format,
        )
        content = completion.choices[0].message.content or "{}"
        return json.loads(content)


def default_model_id() -> str:
    return os.getenv("MARKET_PULSE_RANKER_MODEL", "gpt-6-luna")
