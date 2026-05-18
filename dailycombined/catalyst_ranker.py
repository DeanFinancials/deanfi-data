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
from typing import Protocol


SYSTEM_PROMPT = (
    "You are a deterministic catalyst-ranker for a daily US market recap. "
    "You will receive a JSON list of already-collected catalyst candidates "
    "and a short summary of today's market moves. Your job is to rank the "
    "provided catalysts by how well they explain today's session, returning "
    "ONLY a JSON object of the form {\"ranked_urls\": [\"<url>\", ...]} where "
    "every URL is copied verbatim from the input. Do not invent URLs. Do not "
    "add prose. Do not omit catalysts unless they are clearly irrelevant."
)


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


def _build_messages(payload: dict, market_summary: str) -> list:
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
        for c in payload.get("ranked", [])
    ]
    user_content = json.dumps({
        "market_summary": market_summary,
        "candidates": minimal,
    })
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


def ai_rerank(
    payload: dict,
    *,
    market_summary: str,
    model_id: str,
    client: RankerClient,
) -> dict:
    """Apply AI ranking to ``payload`` or return it unchanged on failure."""
    by_url = {c.get("url"): c for c in payload.get("ranked", []) if c.get("url")}
    if not by_url:
        return payload

    messages = _build_messages(payload, market_summary)
    try:
        raw = client.rank(
            model=model_id,
            messages=messages,
            response_format=RANKER_RESPONSE_FORMAT,
        )
    except Exception:
        return payload

    if not isinstance(raw, dict):
        return payload
    ordered_urls = raw.get("ranked_urls")
    if not isinstance(ordered_urls, list):
        return payload

    seen: set[str] = set()
    new_ranked = []
    for url in ordered_urls:
        if not isinstance(url, str):
            continue
        if url in seen or url not in by_url:
            continue
        seen.add(url)
        new_ranked.append(by_url[url])

    # If no AI-supplied URL survived validation, the order is identical to
    # the deterministic input; don't relabel it as "ai" — that would be
    # misleading for downstream telemetry.
    if not seen:
        return payload

    # Append any catalyst the model omitted so completeness rules still hold.
    for url, catalyst in by_url.items():
        if url not in seen:
            new_ranked.append(catalyst)

    out = dict(payload)
    out["ranked"] = new_ranked
    metadata = dict(payload.get("metadata") or {})
    metadata["previous_ranking_method"] = metadata.get("ranking_method", "deterministic")
    metadata["ranking_method"] = "ai"
    metadata["ranker_model"] = model_id
    out["metadata"] = metadata
    return out


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
    return os.getenv("MARKET_PULSE_RANKER_MODEL", "gpt-5-nano")
