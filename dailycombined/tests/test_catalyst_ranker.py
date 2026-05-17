"""Tests for the optional low-token Catalyst Ranker (OpenAI)."""

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DAILYCOMBINED_DIR = REPO_ROOT / "dailycombined"
sys.path.insert(0, str(DAILYCOMBINED_DIR))

import catalyst_ranker  # noqa: E402


def _payload():
    return {
        "metadata": {
            "market_date": "2026-05-15",
            "generated_at": "2026-05-15T21:05:00Z",
            "weekly_mode": False,
            "expected_min_catalysts": 3,
            "ranking_method": "deterministic",
        },
        "ranked": [
            {"title": "FOMC", "url": "https://federalreserve.gov/a",
             "source": "Federal Reserve", "source_tier": "official",
             "published_at": "2026-05-15T18:00:00+00:00",
             "category": "monetary_policy", "relevance_score": 80.0,
             "why_it_matters": "rate decision"},
            {"title": "CPI", "url": "https://www.bls.gov/cpi",
             "source": "BLS", "source_tier": "official",
             "published_at": "2026-05-13T12:30:00+00:00",
             "category": "labor_inflation", "relevance_score": 60.0,
             "why_it_matters": "monthly CPI"},
            {"title": "Bloomberg recap", "url": "https://www.bloomberg.com/a",
             "source": "Bloomberg", "source_tier": "premium",
             "published_at": "2026-05-15T20:30:00+00:00",
             "category": "market_news", "relevance_score": 50.0,
             "why_it_matters": "session recap"},
        ],
    }


class _FakeClient:
    def __init__(self, response_payload: dict, model: str = "gpt-mini"):
        self._response = response_payload
        self.model_seen = None
        self.calls = []

    def rank(self, *, model: str, messages: list, response_format: dict) -> dict:
        self.model_seen = model
        self.calls.append({"messages": messages, "response_format": response_format})
        return self._response


def test_ai_rerank_reorders_by_returned_order_and_marks_method_ai():
    fake = _FakeClient({
        "ranked_urls": [
            "https://www.bloomberg.com/a",
            "https://federalreserve.gov/a",
            "https://www.bls.gov/cpi",
        ]
    })

    out = catalyst_ranker.ai_rerank(
        _payload(),
        market_summary="SPY +0.3%, energy lead, utilities lag",
        model_id="gpt-mini",
        client=fake,
    )

    assert [c["title"] for c in out["ranked"]] == ["Bloomberg recap", "FOMC", "CPI"]
    assert out["metadata"]["ranking_method"] == "ai"
    assert out["metadata"]["previous_ranking_method"] == "deterministic"
    assert fake.model_seen == "gpt-mini"
    response_format = fake.calls[0]["response_format"]
    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["strict"] is True
    assert response_format["json_schema"]["schema"]["required"] == ["ranked_urls"]


def test_ai_rerank_falls_back_to_deterministic_when_response_invalid():
    fake = _FakeClient({"oops": "no ranked_urls key"})

    out = catalyst_ranker.ai_rerank(
        _payload(),
        market_summary="S&P +0.3%",
        model_id="gpt-mini",
        client=fake,
    )

    assert out["metadata"]["ranking_method"] == "deterministic"
    assert [c["title"] for c in out["ranked"]] == ["FOMC", "CPI", "Bloomberg recap"]


def test_ai_rerank_falls_back_when_client_raises():
    class Boom:
        def rank(self, **_):
            raise RuntimeError("openai down")

    out = catalyst_ranker.ai_rerank(
        _payload(),
        market_summary="anything",
        model_id="gpt-mini",
        client=Boom(),
    )

    assert out["metadata"]["ranking_method"] == "deterministic"


def test_ai_rerank_refuses_urls_not_in_input_to_prevent_invention():
    fake = _FakeClient({
        "ranked_urls": [
            "https://example.com/INVENTED",  # not in input
            "https://federalreserve.gov/a",
            "https://www.bls.gov/cpi",
            "https://www.bloomberg.com/a",
        ]
    })

    out = catalyst_ranker.ai_rerank(
        _payload(),
        market_summary="anything",
        model_id="gpt-mini",
        client=fake,
    )

    # Invented URL is dropped; remaining respect the AI's order.
    urls = [c["url"] for c in out["ranked"]]
    assert "https://example.com/INVENTED" not in urls
    assert urls == [
        "https://federalreserve.gov/a",
        "https://www.bls.gov/cpi",
        "https://www.bloomberg.com/a",
    ]
    assert out["metadata"]["ranking_method"] == "ai"


def test_ai_rerank_preserves_all_input_catalysts_appending_missing_at_end():
    fake = _FakeClient({
        "ranked_urls": [
            "https://www.bloomberg.com/a",
            # CPI omitted from AI response on purpose
            "https://federalreserve.gov/a",
        ]
    })

    out = catalyst_ranker.ai_rerank(
        _payload(),
        market_summary="anything",
        model_id="gpt-mini",
        client=fake,
    )

    titles = [c["title"] for c in out["ranked"]]
    assert titles[:2] == ["Bloomberg recap", "FOMC"]
    assert "CPI" in titles
