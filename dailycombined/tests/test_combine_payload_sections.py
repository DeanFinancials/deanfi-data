"""Collector files use different top-level envelopes; the combiner must read each one."""

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DAILYCOMBINED_DIR = REPO_ROOT / "dailycombined"
sys.path.insert(0, str(DAILYCOMBINED_DIR))

import combine_daily_snapshots  # noqa: E402


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload))


def test_payload_section_returns_first_present_key():
    payload = {"metadata": {}, "current": {"date": "2026-11-16"}}

    assert combine_daily_snapshots.payload_section(payload, "data", "current") == {"date": "2026-11-16"}
    assert combine_daily_snapshots.payload_section(payload, "data") == {}
    assert combine_daily_snapshots.payload_section(None, "data", default=[]) == []


def test_combine_reads_economy_calendar_and_mean_reversion_envelopes(tmp_path):
    for name in ["growth_output", "inflation_prices", "labor_employment", "money_markets"]:
        _write(
            tmp_path / "economy-breadth" / f"{name}.json",
            {
                "metadata": {"generated_at": "2026-11-17T18:46:21-05:00"},
                "current": {"date": "2026-11-16", "indicators": {"X": {"name": name, "value": 1.0}}},
                "history": {"series": {}},
            },
        )
    _write(
        tmp_path / "earnings-calendar" / "earnings_calendar.json",
        {
            "metadata": {"generated_at": "2026-11-18 12:23:25"},
            "earnings_calendar": [{"symbol": "NVDA", "date": "2026-11-18", "hour": "amc"}],
        },
    )
    _write(
        tmp_path / "meanreversion" / "price_vs_ma_snapshot.json",
        {
            "metadata": {"generated_at": "2026-11-18T13:13:54+00:00"},
            "indices": {"SPY": {"symbol": "SPY", "date": "2026-11-17", "current_price": 732.44}},
        },
    )

    combined = combine_daily_snapshots.combine_snapshots(tmp_path)

    economy = combined["data"]["economy"]
    assert economy["money_markets"]["indicators"]["X"]["name"] == "money_markets"
    assert "history" not in economy["money_markets"]
    assert combined["data"]["weekly"]["earnings_calendar"][0]["symbol"] == "NVDA"
    assert combined["data"]["mean_reversion"]["price_vs_ma"]["SPY"]["current_price"] == 732.44


def test_build_spy_close_requires_matching_market_date():
    data = {"mean_reversion": {"price_vs_ma": {"SPY": {"date": "2026-11-17", "current_price": 732.444}}}}

    assert combine_daily_snapshots.build_spy_close(data, "2026-11-17") == {
        "date": "2026-11-17",
        "close": 732.44,
        "source": "meanreversion/price_vs_ma_snapshot.json",
    }
    assert combine_daily_snapshots.build_spy_close(data, "2026-11-18") is None
    assert combine_daily_snapshots.build_spy_close({}, "2026-11-17") is None
