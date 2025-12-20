# DeanFi Data

**Public market data API updated every 15 minutes during market hours**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Data Updates](https://img.shields.io/badge/updates-every%2015min-brightgreen)](https://github.com/GibsonNeo/deanfi-collectors)
[![Collectors](https://img.shields.io/badge/collectors-7%20active-blue)](https://github.com/GibsonNeo/deanfi-collectors)

Automated market data collection updated by the [deanfi-collectors](https://github.com/GibsonNeo/deanfi-collectors) automation scripts. Free JSON data for developers building financial applications.

## 📊 Available Data

| Dataset | File | Update Frequency | Last Updated |
|---------|------|------------------|--------------|
| **📦 Combined Snapshot** | [`dailycombined/market_snapshot.json`](dailycombined/market_snapshot.json) | Daily after close (4:38pm ET) | See metadata |
| **Daily News** | [`daily-news/top_news.json`](daily-news/top_news.json) | Twice daily (9:30am & 4pm ET) | See metadata |
| **Sector News** | [`daily-news/sector_news.json`](daily-news/sector_news.json) | Twice daily (9:30am & 4pm ET) | See metadata |
| **Major Indexes** | [`major-indexes/`](major-indexes/) | Every 15 min (market hours) | See metadata |
| **Advance/Decline** | [`advance-decline/daily_breadth.json`](advance-decline/daily_breadth.json) | Every 15 min (market hours) | See metadata |
| **A/D Line Historical** | [`advance-decline/ad_line_historical.json`](advance-decline/ad_line_historical.json) | Every 15 min (market hours) | See metadata |
| **MA % Historical** | [`advance-decline/ma_percentage_historical.json`](advance-decline/ma_percentage_historical.json) | Every 15 min (market hours) | See metadata |
| **Mean Reversion** | [`meanreversion/`](meanreversion/) | Every 15 min (market hours) | See metadata |
| **Analyst Trends** | [`analyst-trends/recommendation_trends.json`](analyst-trends/recommendation_trends.json) | Nightly (11pm ET) | See metadata |
| **Sector Analysis** | [`analyst-trends/sector_recommendation_trends.json`](analyst-trends/sector_recommendation_trends.json) | Nightly (11pm ET) | See metadata |
| **Earnings Calendar** | [`earnings-calendar/earnings_calendar.json`](earnings-calendar/earnings_calendar.json) | Nightly (11pm ET) | See metadata |
| **Earnings Surprises** | [`earnings-surprises/earnings_surprises.json`](earnings-surprises/earnings_surprises.json) | Nightly (11pm ET) | See metadata |
| **SP100 Growth** | [`sp100growth/sp100growth.json`](sp100growth/sp100growth.json) | Nightly (11:15pm ET) | See metadata |
| **SP500 Growth** | [`sp500growth/sp500growth.json`](sp500growth/sp500growth.json) | Nightly (11:15pm ET) | See metadata |
| **Implied Volatility** | [`implied-volatility/`](implied-volatility/) | Every 15 min (market hours) | See metadata |
| **Economy Indicators** | [`economy-breadth/`](economy-breadth/) | Twice daily (8am & 12pm ET) | See metadata |
| **Options Whales** | [`options-whales/`](options-whales/) | Twice daily (12pm & 9pm ET) | See metadata |
| **Stock Whales** | [`stock-whales/`](stock-whales/) | Twice daily (12pm & 9pm ET) | See metadata |
| **Support / Resistence** | [`supportresistence/support_resistence.json`](supportresistence/support_resistence.json) | Daily (weekdays) | See metadata |

## 🚀 Quick Start

### 📦 Combined Daily Snapshot (Easiest!)

**NEW:** Get all daily market data in a single API call:

```javascript
// Single request for all market data
const url = 'https://r2.deanfi.com/dailycombined/market_snapshot.json';
const response = await fetch(url);
const snapshot = await response.json();

// Access everything
console.log(snapshot.data.market_breadth);    // S&P 500 breadth
console.log(snapshot.data.major_indexes);     // All index prices
console.log(snapshot.data.news);              // Latest news
console.log(snapshot.data.economy);           // Economic indicators
console.log(snapshot.data.support_resistence); // Pivot points + SMAs (support/resistence)
```

**Includes:** Market breadth, major indexes, mean reversion, implied volatility, news, economy data, and weekly earnings data. Updated daily at 4:38pm ET.

See [`dailycombined/README.md`](dailycombined/README.md) for full documentation.

---

### Cloudflare R2 Access (Recommended)

High-performance edge access via Cloudflare R2:

```javascript
// Fetch individual datasets from R2 (faster, no rate limits)
const url = 'https://r2.deanfi.com/daily-news/top_news.json';
const response = await fetch(url);
const data = await response.json();

console.log(data.metadata); // Check last update time
console.log(data.data);     // Array of news articles
```

**Benefits:**
- ⚡ **Faster**: ~50ms latency (global edge network)
- 🚀 **No rate limits**: Unlimited requests
- 💰 **Free egress**: To Cloudflare services
- 🌍 **Global CDN**: Cached at 300+ locations

### Direct JSON Access (GitHub Raw)

Alternative access via GitHub raw URLs:

```javascript
// Fetch latest news from GitHub
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

### With Edge Caching (Production)

Fetch from R2 with Cloudflare edge caching (recommended for production):

> **Note**: R2 bucket must contain uploaded files. Verify upload via [Cloudflare Dashboard](https://dash.cloudflare.com) → R2 → your-bucket or run workflow manually from GitHub Actions.

```javascript
// Cloudflare Worker or Pages Function
async function fetchMarketData(category, file) {
  // Prefer R2 for better performance
  const r2Url = `https://pub-xxxxx.r2.dev/${category}/${file}`;
  const githubUrl = `https://raw.githubusercontent.com/GibsonNeo/deanfi-data/main/${category}/${file}`;
  
  try {
    // Try R2 first with 15-min cache
    const response = await fetch(r2Url, {
      cf: { 
        cacheTtl: 900,  // 15 minutes
        cacheEverything: true 
      }
    });
    
    if (response.ok) return response;
  } catch (error) {
    console.warn('R2 fetch failed, falling back to GitHub:', error);
  }
  
  // Fallback to GitHub if R2 unavailable
  return fetch(githubUrl, {
    cf: { cacheTtl: 900 }
  });
}

// Use it
const response = await fetchMarketData('daily-news', 'top_news.json');
const data = await response.json();
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

### Cloudflare R2 (Recommended)

**Base URL:** `https://pub-xxxxx.r2.dev/` (replace with your R2 public URL)

Alternative: Configure custom domain → `https://data.deanfinancials.com/`

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

### GitHub Raw URLs (Fallback)

**Base URL:** `https://raw.githubusercontent.com/GibsonNeo/deanfi-data/main/`

Same endpoints as above, append to base URL.

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
3. **Git Storage:** Automated commits push JSON files to this repository (only changed files)
4. **R2 Sync:** GitHub Action uploads changed files to Cloudflare R2 bucket
5. **Distribution:** R2 serves files via global edge network (primary) + GitHub raw URLs (fallback)
6. **Consumption:** Your app fetches JSON from R2 for optimal performance

```
┌─────────────────────────────────────────────────────┐
│  GitHub Actions (deanfi-collectors)                 │
│  ├─ Fetch from APIs (Finnhub, Yahoo Finance)       │
│  ├─ Process & validate data                        │
│  └─ Generate JSON outputs                          │
└────────────┬────────────────────────────────────────┘
             │ git commit (only changed files)
             ▼
┌─────────────────────────────────────────────────────┐
│  deanfi-data repository (this repo)                 │
│  ├─ Store JSON files in Git                        │
│  ├─ Version control & history                      │
│  └─ Trigger R2 sync workflow                       │
└────────────┬────────────────────────────────────────┘
             │ GitHub Action: sync-to-r2.yml
             │ (uploads only changed files)
             ▼
┌─────────────────────────────────────────────────────┐
│  Cloudflare R2 Bucket                               │
│  ├─ Global edge caching                            │
│  ├─ Low latency (~50ms)                            │
│  └─ No rate limits                                 │
└────────────┬────────────────────────────────────────┘
             │
             ├──────────────────┬─────────────────────┐
             ▼                  ▼                     ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  Your Web App    │  │  Mobile App      │  │  Data Analysis   │
│  (Astro/React)   │  │  (Native/Web)    │  │  (Python/R)      │
└──────────────────┘  └──────────────────┘  └──────────────────┘
```

### R2 Sync Details

The R2 sync workflow (`.github/workflows/sync-to-r2.yml`) intelligently uploads only changed files:

- **Trigger**: On push to `main` when `*.json` files change
- **Detection**: Uses `git diff` to identify modified files
- **Upload**: Only syncs files that actually changed (not entire directory)
- **Efficiency**: Reduces upload time and R2 write operations
- **Fallback**: Manual trigger available for full sync if needed

### Cloudflare R2 Authentication (Important)

Wrangler's `r2` commands (e.g. `wrangler r2 object put`) use **Cloudflare API Tokens**, *not* the S3-style R2 Access Keys.

| Use Case | Credential Type | How to Generate | Example Var |
|----------|-----------------|-----------------|-------------|
| CI Uploads via `wrangler r2` | Cloudflare API Token | Dashboard → My Profile → API Tokens → Create Custom Token | `CLOUDFLARE_API_TOKEN` |
| Direct S3 SDK / AWS CLI access | R2 Access Key ID + Secret | R2 Dashboard → Manage Access Keys | `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` |

If you pass an R2 Secret Access Key as `CLOUDFLARE_API_TOKEN`, Wrangler authentication will fail with `403` or error code `10000`.

#### Minimum API Token Permissions (Least Privilege)
Grant: `Account R2 Storage:Edit` (includes read & write). Optionally add `Account R2 Storage:Read` explicitly if UI lists separately.

No Workers or Zone permissions are required for pure bucket/object operations.

#### Create the Correct API Token
1. Cloudflare Dashboard → My Profile → API Tokens → Create Token
2. Select "Create Custom Token"
3. Add permission: `Account R2 Storage:Edit`
4. (Optional) Add `Account R2 Storage:Read`
5. Scope: The target account containing the `deanfi-data` bucket
6. Create & copy token → store as GitHub Secret `CLOUDFLARE_API_TOKEN`

#### CI Secret Requirements
| Secret | Description |
|--------|-------------|
| `CLOUDFLARE_ACCOUNT_ID` | Account ID (from dashboard URL) |
| `CLOUDFLARE_API_TOKEN` | Cloudflare API Token (not R2 access key) |
| `R2_BUCKET_NAME` | Bucket name (e.g. `deanfi-data`) |

#### Validation Step (Added)
Workflow now runs:
```bash
wrangler whoami
wrangler r2 bucket list --remote
```
If bucket not found or auth fails, the job stops early with guidance.

#### Troubleshooting Matrix
| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `403 Forbidden` on every upload | Using R2 access key instead of API token | Create proper API Token (see above) |
| `Authentication error 10000` listing buckets | Token lacks R2 Storage scope | Recreate token with `Account R2 Storage:Edit` |
| Uploads show success but objects missing | Missing `--remote` flag (local mode) | Ensure `--remote` is present |
| Bucket not listed | Wrong account or bucket name | Verify `CLOUDFLARE_ACCOUNT_ID` and bucket exists |

#### Optional Improvement
You can rename the secret to `CLOUDFLARE_R2_API_TOKEN` for clarity (workflow currently uses `CLOUDFLARE_API_TOKEN`).


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
