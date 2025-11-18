# Earnings Calendar

Upcoming earnings releases updated weekly on Sundays at 12:00pm ET.

## Files

- **`earnings_calendar.json`** - 30 days forward of earnings releases with EPS and revenue estimates

## Data Format

```json
{
  "metadata": {
    "generated_at": "2025-11-17T22:00:00Z",
    "source": "Finnhub API",
    "total_companies": 250,
    "date_range": {
      "from": "2025-11-17",
      "to": "2025-12-17"
    }
  },
  "data": [
    {
      "symbol": "AAPL",
      "date": "2025-11-20",
      "epsActual": null,
      "epsEstimate": 1.52,
      "hour": "amc",
      "quarter": 4,
      "revenueActual": null,
      "revenueEstimate": 85000000000,
      "year": 2025
    }
  ]
}
```

## Timing Codes

- **`bmo`** - Before Market Open
- **`amc`** - After Market Close  
- **`dmh`** - During Market Hours
- **`null`** - Time Not Specified

## Update Schedule

- **Frequency:** Weekly
- **Day/Time:** Sunday 12:00pm ET
- **Range:** 30 days forward

## Access

```javascript
const url = 'https://raw.githubusercontent.com/GibsonNeo/deanfi-data/main/earnings-calendar/earnings_calendar.json';
```

## Collector Script

Data is collected by: [`deanfi-collectors/earningscalendar`](https://github.com/GibsonNeo/deanfi-collectors/tree/main/earningscalendar)
