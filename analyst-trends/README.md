# Analyst Trends

Analyst recommendation trends updated weekly on Sundays at 12:00pm ET.

## Files

- **`recommendation_trends.json`** - Buy/hold/sell recommendation changes for S&P 500 stocks
- **`sector_recommendation_trends.json`** - Aggregated recommendations grouped by GICS sector

## Data Format

```json
{
  "metadata": {
    "generated_at": "2025-11-17T22:00:00Z",
    "source": "Finnhub API",
    "total_tickers": 503,
    "num_periods": 3
  },
  "data": {
    "AAPL": [
      {
        "buy": 25,
        "hold": 10,
        "sell": 2,
        "strongBuy": 15,
        "strongSell": 0,
        "period": "2025-11-01",
        "symbol": "AAPL"
      }
    ]
  }
}
```

## Update Schedule

- **Frequency:** Weekly
- **Day/Time:** Sunday 12:00pm ET

## Access

```javascript
const url = 'https://raw.githubusercontent.com/GibsonNeo/deanfi-data/main/analyst-trends/recommendation_trends.json';
```

## Collector Script

Data is collected by: [`deanfi-collectors/analysttrends`](https://github.com/GibsonNeo/deanfi-collectors/tree/main/analysttrends)
