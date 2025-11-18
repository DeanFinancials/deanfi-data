# Implied Volatility

VIX and options volatility data updated every 15 minutes during market hours (9:30am - 4:15pm ET).

## Files

- **`vix_data.json`** - VIX index and related volatility metrics
- **`major_indices_iv.json`** - Implied volatility for major indexes
- **`sector_etfs_iv.json`** - Implied volatility for sector ETFs

## Data Format

```json
{
  "metadata": {
    "generated_at": "2025-11-17T15:00:00Z",
    "source": "Yahoo Finance",
    "total_symbols": 15
  },
  "data": {
    "VIX": {
      "symbol": "VIX",
      "value": 15.25,
      "change": -0.50,
      "pct_change": -3.17,
      "timestamp": "2025-11-17T15:00:00Z"
    }
  }
}
```

## Update Schedule

- **Frequency:** Every 15 minutes
- **Hours:** 9:30am - 4:15pm ET
- **Days:** Monday - Friday (market days)

## Access

```javascript
const url = 'https://raw.githubusercontent.com/GibsonNeo/deanfi-data/main/implied-volatility/vix_data.json';
```

## Collector Script

Data is collected by: [`deanfi-collectors/impliedvol`](https://github.com/GibsonNeo/deanfi-collectors/tree/main/impliedvol)
