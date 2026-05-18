import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DAILYCOMBINED_DIR = REPO_ROOT / "dailycombined"
sys.path.insert(0, str(DAILYCOMBINED_DIR))

import combine_daily_snapshots
import validate_market_pulse_input


def test_market_pulse_input_schema_defines_required_package_sections():
    schema_path = DAILYCOMBINED_DIR / "market_pulse_input.schema.json"

    schema = json.loads(schema_path.read_text())

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["title"] == "DeanFi Market Pulse Input"
    assert set(schema["required"]) == {
        "metadata",
        "core",
        "catalysts",
        "optional_context",
        "validation",
        "sources",
    }
    assert "pulse_input_status" in schema["properties"]["metadata"]["required"]
    assert "data_sources" in schema["properties"]["metadata"]["required"]


def test_write_combined_outputs_writes_market_snapshot_and_market_pulse_input(tmp_path):
    combined = {
        "metadata": {
            "market_date": "2026-05-15",
            "previous_market_date": "2026-05-14",
            "generated_at": "2026-05-15T21:20:00Z",
            "timezone": "America/New_York",
            "data_sources": [],
            "blocks": {},
        },
        "data": {"writer_ready": {}},
    }

    combine_daily_snapshots.write_combined_outputs(combined, tmp_path)

    assert (tmp_path / "market_snapshot.json").exists()
    pulse_input = json.loads((tmp_path / "market_pulse_input.json").read_text())
    assert pulse_input["metadata"]["market_date"] == "2026-05-15"
    assert pulse_input["metadata"]["previous_market_date"] == "2026-05-14"


def test_write_combined_outputs_preserves_market_snapshot_payload(tmp_path):
    combined = {
        "metadata": {
            "market_date": "2026-05-15",
            "generated_at": "2026-05-15T21:20:00Z",
            "timezone": "America/New_York",
            "data_sources": [{"category": "existing"}],
            "blocks": {"existing": {"status": "ok"}},
            "total_sources": 1,
            "categories_included": ["major_indexes"],
        },
        "data": {
            "major_indexes": {"us_major": {"^GSPC": {"current_price": 6500}}},
            "writer_ready": {},
        },
    }

    combine_daily_snapshots.write_combined_outputs(combined, tmp_path)

    assert json.loads((tmp_path / "market_snapshot.json").read_text()) == combined


def test_market_pulse_input_core_contains_all_required_article_datasets():
    combined = {
        "metadata": {
            "market_date": "2026-05-15",
            "generated_at": "2026-05-15T21:20:00Z",
            "timezone": "America/New_York",
            "data_sources": [],
        },
        "data": {
            "writer_ready": {
                "major_indexes_table": [{"symbol": "^GSPC"}],
                "index_table_5day": {"dates": ["2026-05-11"]},
                "breadth_table": {"advances": 300},
                "breadth_lookback_5day": {"dates": ["2026-05-11"]},
                "sector_leaders": [{"symbol": "XLK"}],
                "sector_laggards": [{"symbol": "XLE"}],
                "volatility_summary": {"vix": {"close": 14.2}},
                "vix_table_5day": {"dates": ["2026-05-11"]},
                "technical_levels": {"SPY": {"sma": {}}},
                "spy_sma_table_5day": {"dates": ["2026-05-11"]},
            }
        },
    }

    pulse_input = combine_daily_snapshots.build_market_pulse_input(combined)

    assert pulse_input["core"] == {
        "major_index_closes": [{"symbol": "^GSPC"}],
        "five_session_index_returns": {"dates": ["2026-05-11"]},
        "breadth": {"advances": 300},
        "five_session_breadth_lookback": {"dates": ["2026-05-11"]},
        "moving_average_participation": {
            "above_20_day_ma_pct": None,
            "above_50_day_ma_pct": None,
            "above_200_day_ma_pct": None,
        },
        "sector_leaders": [{"symbol": "XLK"}],
        "sector_laggards": [{"symbol": "XLE"}],
        "vix": {"close": 14.2},
        "five_session_vix_lookback": {"dates": ["2026-05-11"]},
        "major_etf_implied_volatility": [],
        "spy_technical_levels": {"sma": {}},
        "five_session_spy_sma": {"dates": ["2026-05-11"]},
    }


def test_market_pulse_input_optional_context_uses_explicit_status_vocabulary():
    combined = {
        "metadata": {
            "market_date": "2026-05-15",
            "generated_at": "2026-05-15T21:20:00Z",
            "timezone": "America/New_York",
            "data_sources": [],
            "blocks": {
                "economy": {"status": "ok", "source": "economy-breadth/*.json", "record_count": 4},
                "weekly": {"status": "empty", "reason": "No weekly data", "source": "earnings-calendar/*.json"},
                "fund_flows": {"status": "stale", "reason": "Older than freshness window"},
                "stock_whales": {"status": "low_relevance", "reason": "No article-worthy signal"},
            },
        },
        "data": {
            "writer_ready": {},
            "economy": {"money_markets": {"fed_funds": 5.33}},
            "weekly": {},
            "fund_flows": {"asset_class": []},
            "stock_whales": {"summary": []},
        },
    }

    optional_context = combine_daily_snapshots.build_market_pulse_input(combined)["optional_context"]

    assert optional_context["economy"]["status"] == "included"
    assert optional_context["economy"]["data"] == {"money_markets": {"fed_funds": 5.33}}
    assert optional_context["earnings"]["status"] == "omitted_empty"
    assert optional_context["fund_flows"]["status"] == "omitted_stale"
    assert optional_context["stock_whales"]["status"] == "omitted_low_relevance"
    assert optional_context["options_whales"]["status"] == "omitted_empty"


def test_combine_snapshots_wires_optional_context_modules_from_repo_data():
    combined = combine_daily_snapshots.combine_snapshots(REPO_ROOT)

    assert "fund_flows" in combined["metadata"]["blocks"]
    assert "options_whales" in combined["metadata"]["blocks"]
    assert "stock_whales" in combined["metadata"]["blocks"]
    assert "fund_flows" in combined["data"]
    assert "options_whales" in combined["data"]
    assert "stock_whales" in combined["data"]

    optional_context = combine_daily_snapshots.build_market_pulse_input(combined)["optional_context"]

    valid_live_statuses = {"included", "omitted_low_relevance", "omitted_stale"}
    assert optional_context["fund_flows"]["status"] in valid_live_statuses
    assert optional_context["options_whales"]["status"] in valid_live_statuses
    assert optional_context["stock_whales"]["status"] in valid_live_statuses


def test_market_pulse_input_reports_sources_freshness_and_blocking_failures():
    combined = {
        "metadata": {
            "market_date": "2026-05-15",
            "generated_at": "2026-05-15T21:20:00Z",
            "timezone": "America/New_York",
            "data_sources": [
                {
                    "category": "market_breadth",
                    "source": "advance-decline/daily_breadth.json",
                    "last_updated": "2026-05-15T21:05:00Z",
                }
            ],
            "blocks": {
                "market_breadth": {"status": "ok"},
                "major_indexes": {"status": "missing", "reason": "No major index file"},
                "implied_volatility": {"status": "ok"},
                "support_resistence": {"status": "ok"},
                "writer_ready": {"status": "empty", "reason": "No writer tables"},
            },
        },
        "data": {"writer_ready": {"breadth_table": {"advances": 300}}},
    }

    pulse_input = combine_daily_snapshots.build_market_pulse_input(combined)

    assert pulse_input["metadata"]["pulse_input_status"] == "partial"
    assert pulse_input["metadata"]["data_sources"] == [
        {
            "category": "market_breadth",
            "source": "advance-decline/daily_breadth.json",
            "last_updated": "2026-05-15T21:05:00Z",
        }
    ]
    assert pulse_input["sources"]["r2_url"] == "https://r2.deanfi.com/dailycombined/market_pulse_input.json"
    assert pulse_input["validation"]["is_valid"] is False
    assert "missing core.major_index_closes" in pulse_input["validation"]["blocking_failures"]
    assert "missing core.five_session_index_returns" in pulse_input["validation"]["blocking_failures"]


def test_market_pulse_input_marks_catalysts_as_phase_two_placeholder():
    pulse_input = combine_daily_snapshots.build_market_pulse_input({
        "metadata": {
            "market_date": "2026-05-15",
            "generated_at": "2026-05-15T21:20:00Z",
            "timezone": "America/New_York",
            "data_sources": [],
        },
        "data": {"writer_ready": {}},
    })

    assert pulse_input["catalysts"] == {
        "status": "phase_2_pending",
        "ranked": [],
        "note": "Catalyst collection and ranking are implemented in Phase 2; do not interpret an empty ranked list as no catalysts for the session.",
    }


def test_validate_market_pulse_input_file_rejects_blocking_failures(tmp_path):
    input_path = tmp_path / "market_pulse_input.json"
    input_path.write_text(json.dumps({
        "metadata": {},
        "core": {},
        "catalysts": {"ranked": []},
        "optional_context": {},
        "validation": {
            "is_valid": False,
            "blocking_failures": ["missing core.major_index_closes"],
        },
        "sources": {},
    }))

    result = validate_market_pulse_input.validate_file(input_path)

    assert result.ok is False
    assert "missing core.major_index_closes" in result.errors


def test_validate_market_pulse_input_file_uses_schema_contract(tmp_path):
    input_path = tmp_path / "market_pulse_input.json"
    input_path.write_text(json.dumps({
        "metadata": {
            "market_date": "2026-05-15",
            "generated_at": "2026-05-15T21:20:00Z",
            "timezone": "America/New_York",
            "pulse_input_status": "ready",
            "data_sources": [],
        },
        "core": {},
        "catalysts": {"ranked": []},
        "optional_context": {},
        "validation": {"is_valid": True, "blocking_failures": []},
        "sources": {},
        "unexpected": True,
    }))

    result = validate_market_pulse_input.validate_file(input_path)

    assert result.ok is False
    assert any("Additional properties are not allowed" in error for error in result.errors)


def test_generated_market_pulse_input_conforms_to_schema():
    combined = combine_daily_snapshots.combine_snapshots(REPO_ROOT)
    pulse_input = combine_daily_snapshots.build_market_pulse_input(combined)

    schema_errors = validate_market_pulse_input.collect_schema_errors(pulse_input)

    assert schema_errors == []


def test_combine_workflow_validates_and_uploads_market_pulse_input():
    workflow = (REPO_ROOT / ".github" / "workflows" / "combine-daily-snapshots.yml").read_text()

    dependency_install = workflow.index("python -m pip install jsonschema openai")
    combine_step = workflow.index("python combine_daily_snapshots.py")
    snapshot_upload = workflow.index("$R2_BUCKET_NAME/dailycombined/market_snapshot.json")
    pulse_validation = workflow.index("python dailycombined/validate_market_pulse_input.py dailycombined/market_pulse_input.json")

    assert dependency_install < combine_step
    assert snapshot_upload < pulse_validation
    assert 'OPENAI_API_KEY: "${{ secrets.OPENAI_API_KEY }}"' in workflow
    assert 'MARKET_PULSE_RANKER_MODEL: "${{ vars.MARKET_PULSE_RANKER_MODEL }}"' in workflow
    assert "python -m pip install jsonschema openai" in workflow
    assert "python dailycombined/validate_market_pulse_input.py dailycombined/market_pulse_input.json" in workflow
    assert "dailycombined/market_pulse_input.json" in workflow
    assert "$R2_BUCKET_NAME/dailycombined/market_pulse_input.json" in workflow
