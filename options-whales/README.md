# Options Whale Trades Data

This directory contains S&P 500 options whale trade data collected from Alpaca Markets.

## Files

| File | Description | Update Frequency |
|------|-------------|------------------|
| `options_whale_summary.json` | Aggregate sentiment and sector analysis | Daily @ 9 PM ET |
| `options_whale_trades.json` | Per-ticker whale trades with full details | Daily @ 9 PM ET |

## Data Source

- **Provider**: Alpaca Markets Options API
- **Coverage**: S&P 500 constituents
- **Lookback**: 5 trading days (excluding weekends/holidays)

## Summary JSON Structure

```json
{
  "_README": { /* methodology and field descriptions */ },
  "metadata": {
    "generated_at": "2025-12-17T02:00:00Z",
    "tickers_scanned": 503,
    "tickers_with_whales": 142,
    "total_whale_trades": 892
  },
  "overall_sentiment": {
    "direction": "BULLISH",
    "call_premium_total": 45000000,
    "put_premium_total": 32000000,
    "call_put_ratio": 1.41
  },
  "sector_sentiment": {
    "Information Technology": { /* sector metrics */ },
    "Financials": { /* sector metrics */ }
  }
}
```

## Trades JSON Structure

```json
{
  "_README": { /* methodology and field descriptions */ },
  "metadata": { /* same as summary */ },
  "sweeps": [
    {
      "sweep_id": "MS-sweep-1",
      "total_premium": 1250000,
      "legs": 4
    }
  ],
  "by_ticker": {
    "MS": {
      "sentiment": "BULLISH",
      "call_premium": 1500000,
      "put_premium": 200000,
      "trades": [ /* individual trades */ ]
    }
  }
}
```

## Key Metrics

### Sentiment Interpretation

| Direction | Meaning |
|-----------|---------|
| BULLISH | More call premium than put premium |
| BEARISH | More put premium than call premium |
| NEUTRAL | Roughly equal call/put premium |

### Call/Put Ratio

- **> 2.0**: Strongly bullish sentiment
- **1.5 - 2.0**: Bullish sentiment
- **1.0 - 1.5**: Slightly bullish
- **0.5 - 1.0**: Slightly bearish
- **< 0.5**: Strongly bearish sentiment

### Trade Tiers

| Tier | Premium | Significance |
|------|---------|--------------|
| Notable | $10K-$50K | Worth watching |
| Unusual | $50K-$100K | Real money |
| Whale | $100K-$250K | Institutional size |
| Strong Whale | $250K-$1M | Large conviction |
| Headline | $1M+ | Major institutional |

## Usage Notes

1. **Sweep Detection**: Trades marked with `is_sweep: true` are part of rapid multi-leg orders, often indicating aggressive institutional positioning.

2. **Dynamic Thresholds**: Each ticker has an `effective_threshold` that was applied. Mega-cap names have higher thresholds.

3. **OTM Focus**: Only out-of-the-money options are included (more directional, less hedging noise).

4. **Sector Analysis**: Use sector_sentiment in summary JSON for sector rotation signals.

## Related Data

- `/analyst-trends/` - Analyst recommendations
- `/meanreversion/` - Mean reversion signals
- `/major-indexes/` - Index performance

## Data Collection

Collected via [deanfi-collectors](../../../deanfi-collectors/optionswhales/) using Alpaca Markets API.
