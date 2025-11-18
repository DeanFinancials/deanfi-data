# Daily News

Market news data updated twice daily at market open (9:30am ET) and market close (4:00pm ET), Monday-Friday.

## Files

- **`top_news.json`** - Top 100 market news articles, prioritized by source (Bloomberg → CNBC → MarketWatch)
- **`sector_news.json`** - News grouped by GICS sector (max 9 articles per sector, max 3 per ticker)

## Data Format

### top_news.json

```json
{
  "metadata": {
    "generated_at": "2025-11-17T14:30:00Z",
    "source": "Finnhub API",
    "total_articles": 100,
    "lookback_days": 7,
    "source_priority": ["Bloomberg", "CNBC", "MarketWatch"]
  },
  "data": [
    {
      "category": "company news",
      "datetime": 1700236800,
      "headline": "Apple announces new product line",
      "id": 123456789,
      "image": "https://...",
      "related": "AAPL",
      "source": "Bloomberg",
      "summary": "Apple Inc. announced...",
      "url": "https://..."
    }
  ]
}
```

### sector_news.json

```json
{
  "metadata": {
    "generated_at": "2025-11-17T14:30:00Z",
    "source": "Finnhub API",
    "total_sectors": 11,
    "max_articles_per_sector": 9,
    "max_articles_per_ticker": 3
  },
  "data": {
    "Information Technology": [
      {
        "category": "company news",
        "datetime": 1700236800,
        "headline": "Microsoft announces cloud expansion",
        "related": "MSFT",
        "source": "CNBC",
        "url": "https://..."
      }
    ],
    "Financials": [...],
    "Health Care": [...]
  }
}
```

## Update Schedule

- **Frequency:** Twice daily
- **Times:** 9:30am ET (market open) and 4:00pm ET (market close)
- **Days:** Monday - Friday (market days)
- **Lookback:** Last 7 days of news

## Access

```javascript
// Fetch top news
const url = 'https://raw.githubusercontent.com/GibsonNeo/deanfi-data/main/daily-news/top_news.json';
const response = await fetch(url);
const data = await response.json();
```

## Collector Script

Data is collected by: [`deanfi-collectors/dailynews`](https://github.com/GibsonNeo/deanfi-collectors/tree/main/dailynews)
