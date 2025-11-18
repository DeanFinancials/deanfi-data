# Advance/Decline Data

Market breadth indicators updated every 15 minutes during market hours (9:30am - 4:15pm ET).

## Files

- **`daily_breadth.json`** - Daily advances, declines, and volume metrics
- **`ad_line_historical.json`** - 1-year historical advance/decline line
- **`ma_percentage_historical.json`** - Moving average breadth (50-day & 200-day)
- **`highs_lows_historical.json`** - 52-week highs and lows percentage

## Data Format

### daily_breadth.json

```json
{
  "metadata": {
    "generated_at": "2025-11-17T15:00:00Z",
    "source": "Yahoo Finance",
    "total_tickers": 503,
    "trading_day": "2025-11-17"
  },
  "summary": {
    "advances": 320,
    "declines": 150,
    "unchanged": 33,
    "advance_decline_ratio": 2.13,
    "advancing_volume": 8500000000,
    "declining_volume": 3200000000,
    "volume_ratio": 2.66,
    "new_highs_52w": 45,
    "new_lows_52w": 12,
    "above_50d_ma": 380,
    "above_200d_ma": 420,
    "pct_above_50d_ma": 75.5,
    "pct_above_200d_ma": 83.5
  }
}
```

## Update Schedule

- **Frequency:** Every 15 minutes
- **Hours:** 9:30am - 4:15pm ET
- **Days:** Monday - Friday (market days)

## Access

```javascript
const url = 'https://raw.githubusercontent.com/GibsonNeo/deanfi-data/main/advance-decline/daily_breadth.json';
```

## Collector Script

Data is collected by: [`deanfi-collectors/advancedecline`](https://github.com/GibsonNeo/deanfi-collectors/tree/main/advancedecline)
