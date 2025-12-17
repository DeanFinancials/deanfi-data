# Stock Whales Data

Large stock trade ("whale trade") data for S&P 500 constituents with focus on dark pool (institutional) activity.

## Overview

This directory contains whale trade data collected by the `stockwhales` collector from `deanfi-collectors`. Data is updated daily during market hours.

## Data Files

### `stock_whale_summary.json`

High-level aggregates and sentiment analysis including:

- **Overall Sentiment**: Net buying vs selling across all whale trades
- **Dark Pool Sentiment**: Institutional-specific sentiment (Exchange D trades)
- **Sector Sentiment**: Aggregated by GICS sector
- **Top Bullish/Bearish Trades**: Largest BUY/SELL trades by ticker
- **Exchange Breakdown**: Volume by exchange (dark pool vs lit)
- **Tier Breakdown**: Counts by trade size tier

### `stock_whale_trades.json`

Per-ticker whale trade details including:

- Sentiment analysis per ticker
- Dark pool trade counts and values
- Individual trade records with:
  - Timestamp, price, shares, value
  - Exchange and dark pool indicator
  - Inferred direction and confidence
  - Size tier classification

## Key Concepts

### Dark Pool Trades

Dark pool trades (Exchange D = FINRA ADF) are off-exchange transactions typically executed by institutional investors. High dark pool activity indicates significant institutional positioning.

| Exchange | Description |
|----------|-------------|
| D | Dark Pool (FINRA ADF) - **Institutional** |
| N | NYSE |
| Q | NASDAQ |
| P | NYSE Arca |
| V | IEX |
| ... | Other lit exchanges |

### Direction Inference

Trade direction is inferred using the Lee-Ready algorithm:

- **BUY (95% confidence)**: Trade at/above ask price
- **SELL (95% confidence)**: Trade at/below bid price
- **NEUTRAL**: Trade at midpoint

### High Confidence Trades

Trades with ≥80% direction confidence are considered "high confidence" and tracked separately for more reliable sentiment signals.

### Size Tiers

| Tier | Value Range | Description |
|------|-------------|-------------|
| Notable | $1M - $2.5M | Notable institutional activity |
| Large | $2.5M - $5M | Large block trade |
| Whale | $5M - $10M | Whale-sized institutional trade |
| Mega Whale | $10M+ | Major institutional positioning |

## Collection Parameters

- **Lookback**: 5 trading days (excludes weekends/holidays)
- **Minimum Thresholds**: 5,000 shares OR $1,000,000 value
- **Dynamic Scaling**: Thresholds increase until ≤10 trades per ticker
- **Max per Ticker**: 20 trades

## Update Schedule

| Time | Description |
|------|-------------|
| 12:00 PM ET | Mid-market update |
| 9:00 PM ET | Post-market update |

## Schema Reference

### Summary JSON Structure

```json
{
  "_README": { /* Field documentation */ },
  "metadata": {
    "collection_timestamp": "ISO timestamp",
    "lookback_start": "ISO date",
    "lookback_end": "ISO date",
    "trading_days": 5,
    "tickers_scanned": 503,
    "total_whale_trades": 450
  },
  "overall_sentiment": {
    "direction": "BULLISH|BEARISH|NEUTRAL",
    "high_confidence_direction": "...",
    "buy_value": 0,
    "sell_value": 0,
    "net_value": 0,
    "buy_sell_ratio": 1.5
  },
  "dark_pool_sentiment": {
    "direction": "...",
    "trade_count": 0,
    "total_value": 0,
    "pct_of_whale_volume": 50.0
  },
  "sector_sentiment": {
    "Technology": { /* sentiment stats */ },
    "Financial Services": { /* ... */ }
  }
}
```

### Trades JSON Structure

```json
{
  "_README": { /* Field documentation */ },
  "metadata": { /* Same as summary */ },
  "by_ticker": {
    "AAPL": {
      "sentiment": "BULLISH",
      "dark_pool_count": 5,
      "dark_pool_value": 40000000,
      "trades": [
        {
          "timestamp": "2025-12-17T14:30:00Z",
          "price": 175.50,
          "shares": 50000,
          "value": 8775000,
          "is_dark_pool": true,
          "direction": "BUY",
          "direction_confidence": 95,
          "tier": "Whale"
        }
      ]
    }
  }
}
```

## Use Cases

1. **Institutional Flow Tracking**: Monitor where big money is positioning
2. **Dark Pool Sentiment**: Identify hidden institutional accumulation/distribution
3. **Sector Rotation**: Track which sectors are seeing institutional interest
4. **Trade Ideas**: Follow the smart money into/out of positions
5. **Risk Management**: Identify potential distribution before price drops

## Related Data

- `options-whales/`: Large options trades with sweep detection
- `analyst-trends/`: Analyst recommendations and revisions
- `major-indexes/`: Market indices and breadth metrics
