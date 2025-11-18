# DeanFi Data

**Public market data API updated every 15 minutes during market hours**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Data Updates](https://img.shields.io/badge/updates-every%2015min-brightgreen)](https://github.com/GibsonNeo/deanfi-collectors)
[![Collectors](https://img.shields.io/badge/collectors-7%20active-blue)](https://github.com/GibsonNeo/deanfi-collectors)

Automated market data collection updated by the [deanfi-collectors](https://github.com/GibsonNeo/deanfi-collectors) automation scripts. Free JSON data for developers building financial applications.

## 📊 Available Data

| Dataset | File | Update Frequency | Last Updated |
|---------|------|------------------|--------------|
| **Daily News** | [`daily-news/top_news.json`](daily-news/top_news.json) | Twice daily (9:30am & 4pm ET) | See metadata |
| **Sector News** | [`daily-news/sector_news.json`](daily-news/sector_news.json) | Twice daily (9:30am & 4pm ET) | See metadata |
| **Major Indexes** | [`major-indexes/`](major-indexes/) | Every 15 min (market hours) | See metadata |
| **Advance/Decline** | [`advance-decline/daily_breadth.json`](advance-decline/daily_breadth.json) | Every 15 min (market hours) | See metadata |
| **A/D Line Historical** | [`advance-decline/ad_line_historical.json`](advance-decline/ad_line_historical.json) | Every 15 min (market hours) | See metadata |
| **MA % Historical** | [`advance-decline/ma_percentage_historical.json`](advance-decline/ma_percentage_historical.json) | Every 15 min (market hours) | See metadata |
| **Analyst Trends** | [`analyst-trends/recommendation_trends.json`](analyst-trends/recommendation_trends.json) | Weekly (Sunday 12pm ET) | See metadata |
| **Sector Analysis** | [`analyst-trends/sector_recommendation_trends.json`](analyst-trends/sector_recommendation_trends.json) | Weekly (Sunday 12pm ET) | See metadata |
| **Earnings Calendar** | [`earnings-calendar/earnings_calendar.json`](earnings-calendar/earnings_calendar.json) | Weekly (Sunday 12pm ET) | See metadata |
| **Earnings Surprises** | [`earnings-surprises/earnings_surprises.json`](earnings-surprises/earnings_surprises.json) | Weekly (Sunday 12pm ET) | See metadata |
| **Implied Volatility** | [`implied-volatility/`](implied-volatility/) | Every 15 min (market hours) | See metadata |

## 🚀 Quick Start

### Direct JSON Access

Use GitHub's raw content URLs to fetch data directly:

```javascript
// Fetch latest news
const url = 'https://raw.githubusercontent.com/GibsonNeo/deanfi-data/main/daily-news/top_news.json';
const response = await fetch(url);
const data = await response.json();

console.log(data.metadata); // Check last update time
console.log(data.data);     // Array of news articles
```

### Python Example

```python
import requests

# Fetch earnings calendar
url = 'https://raw.githubusercontent.com/GibsonNeo/deanfi-data/main/earnings-calendar/earnings_calendar.json'
response = requests.get(url)
earnings = response.json()

print(f"Last updated: {earnings['metadata']['generated_at']}")
print(f"Total companies: {earnings['metadata']['total_companies']}")
```

### With Caching (Production)

Add edge caching for better performance:

```javascript
// Cloudflare Worker example
async function fetchMarketData(category, file) {
  const url = `https://raw.githubusercontent.com/GibsonNeo/deanfi-data/main/${category}/${file}`;
  
  const cache = caches.default;
  const cacheKey = new Request(url);
  
  // Check cache first
  let response = await cache.match(cacheKey);
  if (response) return response;
  
  // Fetch from GitHub
  response = await fetch(url);
  
  // Cache for 60 seconds
  const headers = new Headers(response.headers);
  headers.set('Cache-Control', 'public, max-age=60');
  
  const cachedResponse = new Response(response.body, { headers });
  await cache.put(cacheKey, cachedResponse.clone());
  
  return cachedResponse;
}

// Use it
const news = await fetchMarketData('daily-news', 'top_news.json');
const data = await news.json();
```

## 📈 Data Formats

All datasets follow a consistent structure:

### News Data
```json
{
  "metadata": {
    "generated_at": "2025-11-17T14:30:00Z",
    "source": "Finnhub API",
    "total_articles": 100,
    "lookback_days": 7
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

### Earnings Calendar
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

### Market Breadth
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
    "declining_volume": 3200000000
  }
}
```

## 🔗 API Endpoints

All data is accessible via GitHub raw URLs:

**Base URL:** `https://raw.githubusercontent.com/GibsonNeo/deanfi-data/main/`

| Endpoint | Description |
|----------|-------------|
| `daily-news/top_news.json` | Top 100 market news articles |
| `daily-news/sector_news.json` | News grouped by sector (max 9/sector) |
| `analyst-trends/recommendation_trends.json` | Buy/hold/sell recommendation changes |
| `analyst-trends/sector_recommendation_trends.json` | Aggregated by GICS sector |
| `earnings-calendar/earnings_calendar.json` | 30 days forward earnings releases |
| `earnings-surprises/earnings_surprises.json` | Last 4 quarters EPS vs estimates |
| `advance-decline/daily_breadth.json` | Daily market breadth metrics |
| `advance-decline/ad_line_historical.json` | 1-year advance/decline line |
| `advance-decline/ma_percentage_historical.json` | Moving average breadth (50/200 day) |
| `major-indexes/` | Multiple index tracking files |
| `implied-volatility/` | VIX and options volatility data |

## 📅 Update Schedule

| Frequency | Time (ET) | Datasets |
|-----------|-----------|----------|
| **Every 15 min** | 9:30am - 4:15pm Mon-Fri | Market breadth, Major indexes, Implied volatility |
| **Twice daily** | 9:30am & 4:00pm Mon-Fri | Daily news, Sector news |
| **Weekly** | Sunday 12:00pm | Analyst trends, Earnings calendar, Earnings surprises |

## 📊 Data Freshness

Check the `metadata.generated_at` field in each JSON file for the exact update timestamp:

```javascript
const response = await fetch('https://raw.githubusercontent.com/GibsonNeo/deanfi-data/main/daily-news/top_news.json');
const data = await response.json();

console.log(`Data updated: ${data.metadata.generated_at}`);
// Output: "Data updated: 2025-11-17T14:30:00Z"
```

## 🔄 Historical Data

All historical data is available via git history:

```bash
# Clone the repository
git clone https://github.com/GibsonNeo/deanfi-data.git

# View history of a specific file
git log --follow earnings-calendar/earnings_calendar.json

# Get data from a specific date
git checkout `git rev-list -n 1 --before="2025-11-01" main`
cat daily-news/top_news.json
```

## 🛠️ How It Works

1. **Data Collection:** [deanfi-collectors](https://github.com/GibsonNeo/deanfi-collectors) runs on GitHub Actions
2. **Processing:** Python scripts fetch, validate, and format data
3. **Storage:** Automated commits push JSON files to this repository
4. **Distribution:** GitHub serves files via raw URLs (free CDN!)
5. **Consumption:** Your app fetches JSON directly from GitHub

```
┌─────────────────────────────────────────────────────┐
│  GitHub Actions (deanfi-collectors)                 │
│  ├─ Fetch from APIs (Finnhub, Yahoo Finance)       │
│  ├─ Process & validate data                        │
│  └─ Generate JSON outputs                          │
└────────────┬────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────┐
│  Commit to deanfi-data repository                   │
│  ├─ Update JSON files                              │
│  └─ Timestamp: "chore: update news - 2025-11-17"   │
└────────────┬────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────┐
│  GitHub Raw CDN                                     │
│  https://raw.githubusercontent.com/...              │
└────────────┬────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────┐
│  Your Application                                   │
│  ├─ Fetch JSON                                     │
│  ├─ Cache at edge (optional)                       │
│  └─ Display to users                               │
└─────────────────────────────────────────────────────┘
```

## 🤝 Contributing

This is a data repository - automated commits only. To improve the data collection:

- **See the code repository:** [deanfi-collectors](https://github.com/GibsonNeo/deanfi-collectors)
- **Report data issues:** [Open an issue](https://github.com/GibsonNeo/deanfi-data/issues)
- **Request new datasets:** [Start a discussion](https://github.com/GibsonNeo/deanfi-data/discussions)

## ⚠️ Disclaimers

### Data Attribution
- **Finnhub API:** News, earnings, analyst data - [Finnhub Terms](https://finnhub.io/terms)
- **Yahoo Finance:** Market data, indexes, breadth - [Yahoo Terms](https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html)

### Usage Terms
- ✅ Free for personal and commercial use
- ✅ No rate limits (it's just GitHub hosting!)
- ✅ No authentication required
- ⚠️ No guarantees of uptime or accuracy
- ⚠️ Data is provided as-is for informational purposes
- ❌ Not financial advice - do your own research

### Rate Limiting
While there are no API rate limits, please be respectful:
- ✅ Cache responses (60s recommended)
- ✅ Use conditional requests (If-Modified-Since header)
- ❌ Don't hammer the endpoints every second

## 📜 License

- **Code:** MIT License (see [LICENSE](LICENSE))
- **Data:** Subject to original providers' terms (Finnhub, Yahoo Finance)

## 📞 Support & Contact

- **Website:** [DeanFinancials.com](https://deanfinancials.com)
- **Code Repository:** [deanfi-collectors](https://github.com/GibsonNeo/deanfi-collectors)
- **Issues:** [GitHub Issues](https://github.com/GibsonNeo/deanfi-data/issues)
- **Discussions:** [GitHub Discussions](https://github.com/GibsonNeo/deanfi-data/discussions)

## 🌟 Powered By

- [deanfi-collectors](https://github.com/GibsonNeo/deanfi-collectors) - Data collection automation
- [GitHub Actions](https://github.com/features/actions) - Scheduled data updates
- [Finnhub](https://finnhub.io) - Financial data API
- [Yahoo Finance](https://finance.yahoo.com) - Market data
- [DeanFinancials.com](https://deanfinancials.com) - Market analysis platform

---

**⭐ Star this repo if you find it useful! Updates happen automatically every 15 minutes during market hours.**
