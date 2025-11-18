# Major Indexes

Market index tracking updated every 15 minutes during market hours.

## Files

- **`us_major.json`** - S&P 500, Dow, Nasdaq, Russell 2000
- **`sectors.json`** - SPDR sector ETFs (XLK, XLF, XLV, etc.)
- **`growth_value.json`** - Growth vs Value indexes
- **`international.json`** - International market indexes
- **`bonds.json`** - Treasury and bond indexes
- **`commodities.json`** - Gold, oil, commodities

## Data Format

```json
{
  "metadata": {
    "generated_at": "2025-11-17T14:30:00Z",
    "source": "Yahoo Finance",
    "total_indexes": 25
  },
  "data": {
    "SPY": {
      "symbol": "SPY",
      "name": "S&P 500",
      "price": 450.25,
      "change": 5.30,
      "pct_change": 1.19,
      "volume": 75000000,
      "timestamp": "2025-11-17T14:30:00Z"
    }
  }
}
```

## Update Schedule

- **Frequency:** Every 15 minutes
- **Hours:** 9:30am - 4:00pm ET
- **Days:** Monday - Friday (market days)

## Access

```javascript
const url = 'https://raw.githubusercontent.com/GibsonNeo/deanfi-data/main/major-indexes/us_major.json';
```

## Collector Script

Data is collected by: [`deanfi-collectors/majorindexes`](https://github.com/GibsonNeo/deanfi-collectors/tree/main/majorindexes)
