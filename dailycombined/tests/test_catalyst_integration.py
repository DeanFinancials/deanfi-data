"""Tests for Phase 2 catalyst integration into market_pulse_input.json."""

import json
import sys
import types
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DAILYCOMBINED_DIR = REPO_ROOT / "dailycombined"
sys.path.insert(0, str(DAILYCOMBINED_DIR))

import combine_daily_snapshots  # noqa: E402
import catalyst_integration  # noqa: E402


def _ranked_catalyst(**overrides):
    base = {
        "title": "FOMC statement",
        "source": "Federal Reserve",
        "url": "https://www.federalreserve.gov/x.htm",
        "published_at": "2026-05-15T18:00:00+00:00",
        "category": "monetary_policy",
        "relevance_score": 80.0,
        "why_it_matters": "Decision on policy rate",
        "source_tier": "official",
    }
    base.update(overrides)
    return base


def test_load_market_catalysts_returns_payload_when_present(tmp_path):
    path = tmp_path / "daily-news" / "market_catalysts.json"
    path.parent.mkdir(parents=True)
    payload = {
        "metadata": {
            "market_date": "2026-05-15",
            "generated_at": "2026-05-15T21:05:00Z",
            "weekly_mode": False,
            "expected_min_catalysts": 3,
            "ranking_method": "deterministic",
        },
        "ranked": [_ranked_catalyst()],
    }
    path.write_text(json.dumps(payload))

    loaded = catalyst_integration.load_market_catalysts(tmp_path)
    assert loaded == payload


def test_load_market_catalysts_returns_none_when_missing(tmp_path):
    assert catalyst_integration.load_market_catalysts(tmp_path) is None


def test_build_market_pulse_input_uses_real_catalysts_when_provided():
    combined = {
        "metadata": {"market_date": "2026-05-15", "generated_at": "2026-05-15T21:20:00Z", "timezone": "America/New_York", "data_sources": []},
        "data": {"writer_ready": {}},
    }
    catalysts = {
        "metadata": {
            "market_date": "2026-05-15",
            "generated_at": "2026-05-15T21:05:00Z",
            "weekly_mode": False,
            "expected_min_catalysts": 3,
            "ranking_method": "deterministic",
        },
        "ranked": [
            _ranked_catalyst(title="FOMC", url="https://www.federalreserve.gov/a"),
            _ranked_catalyst(title="CPI", source="BLS", url="https://www.bls.gov/cpi", category="labor_inflation"),
            _ranked_catalyst(title="Bloomberg recap", source="Bloomberg", url="https://www.bloomberg.com/r", source_tier="premium", category="market_news"),
        ],
    }

    pulse_input = combine_daily_snapshots.build_market_pulse_input(combined, catalysts=catalysts)

    titles = [c["title"] for c in pulse_input["catalysts"]["ranked"]]
    assert titles == ["FOMC", "CPI", "Bloomberg recap"]
    assert pulse_input["catalysts"]["status"] == "ready"
    assert "phase_2_pending" not in json.dumps(pulse_input["catalysts"])


def test_build_market_pulse_input_falls_back_to_placeholder_when_catalysts_missing():
    combined = {
        "metadata": {"market_date": "2026-05-15", "generated_at": "2026-05-15T21:20:00Z", "timezone": "America/New_York", "data_sources": []},
        "data": {"writer_ready": {}},
    }
    pulse_input = combine_daily_snapshots.build_market_pulse_input(combined, catalysts=None)
    assert pulse_input["catalysts"]["status"] == "phase_2_pending"
    assert pulse_input["catalysts"]["ranked"] == []


def test_validate_catalysts_blocks_when_below_expected_minimum():
    payload = {
        "metadata": {"weekly_mode": False, "expected_min_catalysts": 3},
        "ranked": [_ranked_catalyst()],
    }
    result = catalyst_integration.validate_completeness(payload, market_date="2026-05-15")
    assert result["is_valid"] is False
    assert any("expected at least 3" in err for err in result["errors"])


def test_validate_catalysts_blocks_on_release_day_with_no_official_source():
    # FOMC meeting date in the locked-in calendar.
    release_day = catalyst_integration.MACRO_RELEASE_CALENDAR_2026[0]["date"]
    payload = {
        "metadata": {"weekly_mode": False, "expected_min_catalysts": 3},
        "ranked": [
            _ranked_catalyst(source="Bloomberg", source_tier="premium",
                             url="https://www.bloomberg.com/x"),
            _ranked_catalyst(source="CNBC", source_tier="premium",
                             url="https://www.cnbc.com/y", title="market recap"),
            _ranked_catalyst(source="SeekingAlpha", source_tier="standard",
                             url="https://seekingalpha.com/z", title="sector watch"),
        ],
    }
    result = catalyst_integration.validate_completeness(payload, market_date=release_day)
    assert result["is_valid"] is False
    assert any("official" in err.lower() for err in result["errors"])


def test_validate_catalysts_is_valid_on_release_day_when_official_source_present():
    release_day = catalyst_integration.MACRO_RELEASE_CALENDAR_2026[0]["date"]
    payload = {
        "metadata": {"weekly_mode": False, "expected_min_catalysts": 3},
        "ranked": [
            _ranked_catalyst(),
            _ranked_catalyst(source="Bloomberg", source_tier="premium",
                             url="https://www.bloomberg.com/x", title="market recap"),
            _ranked_catalyst(source="CNBC", source_tier="premium",
                             url="https://www.cnbc.com/y", title="sector watch"),
        ],
    }
    result = catalyst_integration.validate_completeness(payload, market_date=release_day)
    assert result["is_valid"] is True
    assert result["errors"] == []


def test_build_market_pulse_input_auto_reads_market_catalysts_via_combine_snapshots(tmp_path):
    (tmp_path / "daily-news").mkdir()
    (tmp_path / "daily-news" / "market_catalysts.json").write_text(json.dumps({
        "metadata": {"market_date": "2026-05-15", "generated_at": "2026-05-15T21:05:00Z",
                     "weekly_mode": False, "expected_min_catalysts": 3,
                     "ranking_method": "deterministic"},
        "ranked": [
            _ranked_catalyst(),
            _ranked_catalyst(source="Bloomberg", source_tier="premium",
                             url="https://www.bloomberg.com/a", title="Bloomberg recap"),
            _ranked_catalyst(source="CNBC", source_tier="premium",
                             url="https://www.cnbc.com/b", title="Tech leads"),
        ],
    }))

    combined = combine_daily_snapshots.combine_snapshots(tmp_path)
    pulse = combine_daily_snapshots.build_market_pulse_input(combined)

    assert pulse["catalysts"]["status"] == "ready"
    assert [c["title"] for c in pulse["catalysts"]["ranked"]] == ["FOMC statement", "Bloomberg recap", "Tech leads"]


def test_optional_ai_ranker_reorders_loaded_catalysts_when_configured(tmp_path, monkeypatch):
    (tmp_path / "daily-news").mkdir()
    (tmp_path / "daily-news" / "market_catalysts.json").write_text(json.dumps({
        "metadata": {"market_date": "2026-05-15", "generated_at": "2026-05-15T21:05:00Z",
                     "weekly_mode": False, "expected_min_catalysts": 3,
                     "ranking_method": "deterministic"},
        "ranked": [
            _ranked_catalyst(title="FOMC statement", url="https://www.federalreserve.gov/a"),
            _ranked_catalyst(source="Bloomberg", source_tier="premium",
                             url="https://www.bloomberg.com/a", title="Bloomberg recap"),
            _ranked_catalyst(source="CNBC", source_tier="premium",
                             url="https://www.cnbc.com/b", title="Tech leads"),
        ],
    }))

    class FakeRankerClient:
        def __init__(self, _client):
            pass

        def rank(self, *, model, messages, response_format):
            assert model == "gpt-5-nano"
            assert "Major indexes" in messages[1]["content"] or "Daily market snapshot" in messages[1]["content"]
            assert response_format["type"] == "json_schema"
            return {
                "ranked_urls": [
                    "https://www.bloomberg.com/a",
                    "https://www.federalreserve.gov/a",
                    "https://www.cnbc.com/b",
                ]
            }

    monkeypatch.setattr(combine_daily_snapshots.catalyst_ranker, "OpenAIRankerClient", FakeRankerClient)
    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=lambda api_key: object()))
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("MARKET_PULSE_RANKER_MODEL", "gpt-5-nano")

    combined = combine_daily_snapshots.combine_snapshots(tmp_path)
    pulse = combine_daily_snapshots.build_market_pulse_input(combined)

    assert [c["title"] for c in pulse["catalysts"]["ranked"]][:2] == ["Bloomberg recap", "FOMC statement"]
    assert pulse["catalysts"]["ranking_method"] == "ai"


def test_optional_ai_ranker_preserves_deterministic_order_without_api_key(tmp_path, monkeypatch):
    (tmp_path / "daily-news").mkdir()
    (tmp_path / "daily-news" / "market_catalysts.json").write_text(json.dumps({
        "metadata": {"market_date": "2026-05-15", "generated_at": "2026-05-15T21:05:00Z",
                     "weekly_mode": False, "expected_min_catalysts": 3,
                     "ranking_method": "deterministic"},
        "ranked": [
            _ranked_catalyst(title="FOMC statement", url="https://www.federalreserve.gov/a"),
            _ranked_catalyst(source="Bloomberg", source_tier="premium",
                             url="https://www.bloomberg.com/a", title="Bloomberg recap"),
            _ranked_catalyst(source="CNBC", source_tier="premium",
                             url="https://www.cnbc.com/b", title="Tech leads"),
        ],
    }))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    combined = combine_daily_snapshots.combine_snapshots(tmp_path)
    pulse = combine_daily_snapshots.build_market_pulse_input(combined)

    assert [c["title"] for c in pulse["catalysts"]["ranked"]] == ["FOMC statement", "Bloomberg recap", "Tech leads"]
    assert pulse["catalysts"]["ranking_method"] == "deterministic"


def test_apply_market_context_boosts_catalysts_mentioning_todays_leaders():
    catalysts = {
        "metadata": {"weekly_mode": False, "expected_min_catalysts": 3,
                     "market_date": "2026-05-15", "generated_at": "2026-05-15T21:05:00Z",
                     "ranking_method": "deterministic"},
        "ranked": [
            _ranked_catalyst(title="Off-topic story", source="Bloomberg",
                             source_tier="premium", url="https://www.bloomberg.com/x",
                             relevance_score=50.0,
                             why_it_matters="No sector mentions"),
            _ranked_catalyst(title="Energy stocks lead", source="Bloomberg",
                             source_tier="premium", url="https://www.bloomberg.com/y",
                             relevance_score=50.0,
                             why_it_matters="Energy sector rallied on oil prices"),
        ],
    }
    snapshot_writer_ready = {
        "sector_leaders": [{"sector": "Energy", "change_pct": 1.8}],
        "sector_laggards": [{"sector": "Utilities", "change_pct": -1.2}],
    }

    updated = catalyst_integration.apply_market_context(
        catalysts,
        sector_leaders=snapshot_writer_ready["sector_leaders"],
        sector_laggards=snapshot_writer_ready["sector_laggards"],
    )

    by_title = {c["title"]: c for c in updated["ranked"]}
    assert by_title["Energy stocks lead"]["relevance_score"] > by_title["Off-topic story"]["relevance_score"]
    assert "Energy" in by_title["Energy stocks lead"].get("related_data_points", [])
    # After re-scoring the order should also reflect the boost.
    assert updated["ranked"][0]["title"] == "Energy stocks lead"


def test_apply_market_context_does_not_match_substring_overlap():
    """Sector name must not match a generic English word that contains it.

    Regression: the previous naive ``s.lower() in haystack`` matched
    "Energy" against "synergy" or "energy boilerplate", which could
    half-boost the wrong catalyst by ~12 points and reorder the ranked
    list. The word-boundary + title/symbols matcher must avoid that.
    """
    catalysts = {
        "metadata": {
            "weekly_mode": False, "expected_min_catalysts": 3,
            "market_date": "2026-05-15", "generated_at": "2026-05-15T21:05:00Z",
            "ranking_method": "deterministic",
        },
        "ranked": [
            _ranked_catalyst(
                title="Synergy gains reported by management",
                source="Bloomberg", source_tier="premium",
                url="https://www.bloomberg.com/synergy",
                relevance_score=50.0,
                why_it_matters="The CFO highlighted synergy in the call",
            ),
            _ranked_catalyst(
                title="Quiet session",
                source="CNBC", source_tier="premium",
                url="https://www.cnbc.com/quiet",
                relevance_score=49.0,
                why_it_matters="Indexes moved less than 0.1%",
            ),
        ],
    }
    updated = catalyst_integration.apply_market_context(
        catalysts,
        sector_leaders=[{"sector": "Energy"}],
        sector_laggards=[],
    )
    by_title = {c["title"]: c for c in updated["ranked"]}
    # The synergy catalyst must NOT have been boosted.
    assert by_title["Synergy gains reported by management"]["relevance_score"] == 50.0
    assert "Energy" not in by_title["Synergy gains reported by management"].get("related_data_points", [])


def test_apply_market_context_is_idempotent():
    """Second call must not re-boost relevance_score (Phase 3 re-rank safety)."""
    catalysts = {
        "metadata": {
            "weekly_mode": False, "expected_min_catalysts": 3,
            "market_date": "2026-05-15", "generated_at": "2026-05-15T21:05:00Z",
            "ranking_method": "deterministic",
        },
        "ranked": [
            _ranked_catalyst(
                title="Energy stocks lead",
                source="Bloomberg", source_tier="premium",
                url="https://www.bloomberg.com/y",
                relevance_score=50.0,
                why_it_matters="Sector rally",
            ),
        ],
    }
    once = catalyst_integration.apply_market_context(
        catalysts, sector_leaders=[{"sector": "Energy"}],
    )
    twice = catalyst_integration.apply_market_context(
        once, sector_leaders=[{"sector": "Energy"}],
    )
    assert once["ranked"][0]["relevance_score"] == twice["ranked"][0]["relevance_score"]
    assert twice["metadata"]["market_context_applied"] is True


def test_validate_completeness_blocks_when_calendar_year_missing():
    """Stale calendar (no entries for the market year) must produce a blocking failure."""
    payload = {
        "metadata": {"weekly_mode": False, "expected_min_catalysts": 1},
        "ranked": [_ranked_catalyst()],
    }
    # 2099 is well outside the 2026 calendar coverage.
    result = catalyst_integration.validate_completeness(payload, market_date="2099-05-15")
    assert result["is_valid"] is False
    assert any("calendar stale" in err for err in result["errors"])


def test_load_market_catalysts_raises_on_malformed_json(tmp_path):
    """Half-written file must not look like 'Phase 2 not deployed'."""
    path = tmp_path / "daily-news" / "market_catalysts.json"
    path.parent.mkdir(parents=True)
    path.write_text("{not valid json")
    try:
        catalyst_integration.load_market_catalysts(tmp_path)
    except catalyst_integration.CatalystLoadError:
        return
    raise AssertionError("expected CatalystLoadError")


def test_build_market_pulse_input_blocks_on_catalyst_load_error(tmp_path):
    """Malformed market_catalysts.json must block publication, not silently route to placeholder."""
    (tmp_path / "daily-news").mkdir()
    (tmp_path / "daily-news" / "market_catalysts.json").write_text("{garbage")
    combined = combine_daily_snapshots.combine_snapshots(tmp_path)
    pulse = combine_daily_snapshots.build_market_pulse_input(combined)
    assert pulse["catalysts"]["status"] == "load_error"
    assert pulse["validation"]["is_valid"] is False
    assert any("unreadable" in err for err in pulse["validation"]["blocking_failures"])


def test_required_official_release_today_returns_flat_shape():
    """Phase 3 truthy check `if catalysts.official_release_today:` must work."""
    fomc_date = catalyst_integration.MACRO_RELEASE_CALENDAR_2026[0]["date"]
    on_release = catalyst_integration.required_official_release_today(fomc_date)
    assert on_release["official_release_today"] is True
    assert "FOMC" in on_release["official_release_kinds"]

    off_release = catalyst_integration.required_official_release_today("2026-05-15")
    assert off_release["official_release_today"] is False
    assert off_release["official_release_kinds"] == []
    # Critically: the boolean field must evaluate falsy on non-release days
    # (the previous nested-dict shape was always truthy).
    assert not off_release["official_release_today"]


def test_build_market_pulse_input_propagates_catalyst_blocking_failure():
    combined = {
        "metadata": {"market_date": "2026-05-15", "generated_at": "2026-05-15T21:20:00Z", "timezone": "America/New_York", "data_sources": []},
        "data": {"writer_ready": {}},
    }
    catalysts = {
        "metadata": {"weekly_mode": False, "expected_min_catalysts": 3, "market_date": "2026-05-15", "generated_at": "2026-05-15T21:05:00Z", "ranking_method": "deterministic"},
        "ranked": [_ranked_catalyst()],  # only 1 catalyst, min is 3
    }
    pulse_input = combine_daily_snapshots.build_market_pulse_input(combined, catalysts=catalysts)
    assert pulse_input["validation"]["is_valid"] is False
    assert any("catalysts" in err.lower() for err in pulse_input["validation"]["blocking_failures"])
