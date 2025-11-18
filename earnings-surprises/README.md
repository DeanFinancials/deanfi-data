# Earnings Surprises

Historical earnings surprises (actual vs estimate) updated weekly on Sundays at 12:00pm ET.

## Files

- **`earnings_surprises.json`** - Last 4 quarters of EPS surprises for S&P 500 companies

## Data Format

```json
{
  "metadata": {
    "generated_at": "2025-11-17T22:00:00Z",
    "source": "Finnhub API",
    "total_tickers": 503,
    "quarters_to_fetch": 4
  },
  "data": {
    "AAPL": [
      {
        "actual": 1.46,
        "estimate": 1.39,
        "period": "2025-09-30",
        "quarter": 4,
        "surprise": 0.07,
        "surprisePercent": 5.04,
        "symbol": "AAPL",
        "year": 2025
      }
    ]
  }
}
```

## Metrics

- **`actual`** - Reported EPS
- **`estimate`** - Analyst consensus estimate
- **`surprise`** - Difference (actual - estimate)
- **`surprisePercent`** - Percentage surprise ((actual - estimate) / estimate * 100)

## Update Schedule

- **Frequency:** Weekly
- **Day/Time:** Sunday 12:00pm ET
- **History:** Last 4 quarters

## Access

```javascript
const url = 'https://raw.githubusercontent.com/GibsonNeo/deanfi-data/main/earnings-surprises/earnings_surprises.json';
```

## Collector Script

Data is collected by: [`deanfi-collectors/earningssurprises`](https://github.com/GibsonNeo/deanfi-collectors/tree/main/earningssurprises)
