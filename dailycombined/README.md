# Daily Combined Market Snapshot

**Comprehensive daily market data aggregated into a single JSON file for easy consumption.**

## Overview

The `market_snapshot.json` file combines all daily snapshot data from various market data collectors into one unified structure. This eliminates the need for multiple API calls and simplifies data consumption for client applications.

## Update Schedule

- **Frequency:** Every weekday (Monday-Friday) at **4:38 PM ET** (21:38 UTC)
- **Timing:** Runs 3 minutes after the last daily market data workflow completes
- **Weekends:** No updates on Saturday/Sunday (markets closed)

## Data Included

### 1. Market Breadth (`market_breadth`)
**Source:** `advance-decline/daily_breadth.json`

Comprehensive S&P 500 breadth indicators:
- Advances/Declines counts and ratios
- Volume metrics (advancing vs declining volume)
- 52-week highs and lows percentages
- Moving average participation (20-day, 50-day, 200-day MA)
- Cumulative advance-decline line

### 2. Major Indexes (`major_indexes`)
**Sources:** `major-indexes/*.json` (snapshot versions)

Latest prices and changes for:
- **US Major Indices:** S&P 500, Dow Jones, Nasdaq, Russell 2000
- **US Sectors:** All 11 GICS sectors (XLK, XLF, XLV, etc.)
- **Growth vs Value:** Growth and value style indices
- **International:** Major global indices (FTSE, DAX, Nikkei, etc.)
- **Bonds:** Treasury indices across different maturities
- **Commodities:** Gold, oil, copper, agricultural commodities

### 3. Mean Reversion (`mean_reversion`)
**Sources:** `meanreversion/*_snapshot.json`

Mean reversion opportunity indicators:
- **MA Spreads:** Distance of major indices from their moving averages
- **Price vs MA:** Percentage deviation from key moving averages
- Identifies oversold/overbought conditions

### 4. Implied Volatility (`implied_volatility`)
**Sources:** `implied-volatility/*_snapshot.json`

Current volatility levels:
- **VIX Options:** VIX term structure and skew analysis
- **Major Indices:** IV levels for SPX, NDX, RUT
- **Sector ETFs:** Volatility across all 11 sectors

### 5. News (`news`)
**Sources:** `daily-news/*.json`

Latest market news:
- **Top News:** Top 25 general market news stories
- **Sector News:** News organized by GICS sector

**Writer-friendly (additive):** the combined snapshot also includes `data.news.normalized` with consistent fields:
- `title`, `summary`, `source`, `url`, `published_at`, plus optional `ticker`

### 6. Economy (`economy`)
**Sources:** `economy-breadth/*.json`

Economic indicators:
- **Growth & Output:** GDP, retail sales, industrial production
- **Inflation & Prices:** CPI, PPI, PCE, commodity prices
- **Labor & Employment:** Unemployment, jobless claims, NFP
- **Money Markets:** Fed funds rate, treasury yields, money supply

### 7. Weekly Data (`weekly`) *(when available)*
**Sources:** `earnings-calendar/*.json`, `earnings-surprises/*.json`

Updated weekly on Sundays:
- **Earnings Calendar:** Upcoming earnings announcements
- **Earnings Surprises:** Recent earnings beats/misses

### 8. Support / Resistence (`support_resistence`)
**Source:** `supportresistence/support_resistence.json`

Daily support/resistence reference levels for major index ETFs:
- Traditional pivots: `P, R1, R2, S1, S2`
- Fibonacci pivots: `FP, FR1, FR2, FS1, FS2`
- Trend references: `SMA20, SMA50, SMA200`

## File Structure

```json
{
  "metadata": {
    "market_date": "2025-11-25",
    "date": "2025-11-25",
    "previous_market_date": "2025-11-22",
    "timezone": "America/New_York",
    "generated_at": "2025-11-25T21:38:00.000000+00:00",
    "description": "Combined daily market snapshot from all data collectors",
    "update_schedule": "Updated after market close (approximately 4:38pm ET on weekdays)",
    "blocks": {
      "market_breadth": { "status": "ok" },
      "major_indexes": { "status": "ok" },
      "news_top": { "status": "ok" },
      "news_sectors": { "status": "ok" },
      "writer_ready": { "status": "ok" }
    },
    "total_sources": 20,
    "categories_included": ["market_breadth", "major_indexes", ...],
    "data_sources": [
      {
        "category": "market_breadth",
        "source": "advance-decline/daily_breadth.json",
        "last_updated": "2025-11-25T21:35:00.000000+00:00"
      },
      ...
    ]
  },
  "data": {
    "market_breadth": { ... },
    "major_indexes": {
      "us_major": { ... },
      "us_sectors": { ... },
      "us_growth_value": { ... },
      "international": { ... },
      "bonds": { ... },
      "commodities": { ... }
    },
    "mean_reversion": {
      "ma_spreads": { ... },
      "price_vs_ma": { ... }
    },
    "implied_volatility": {
      "vix_options": { ... },
      "major_indices": { ... },
      "sector_etfs": { ... }
    },
    "news": {
      "top_news": [ ... ],
      "sector_news": { ... },
      "normalized": {
        "top_news": [
          {
            "title": "...",
            "summary": "...",
            "source": "...",
            "url": "...",
            "published_at": "...",
            "timestamp": 0,
            "category": "...",
            "id": 0,
            "ticker": "AAPL"
          }
        ],
        "sector_news": {
          "XLK": {
            "sector_name": "Information Technology",
            "articles": [ ... ]
          }
        }
      }
    },
    "economy": {
      "growth_output": { ... },
      "inflation_prices": { ... },
      "labor_employment": { ... },
      "money_markets": { ... }
    },
    "weekly": {
      "earnings_calendar": { ... },
      "earnings_surprises": { ... }
    },
    "writer_ready": {
      "breadth_table": {
        "market_date": "YYYY-MM-DD",
        "advances": 0,
        "declines": 0,
        "unchanged": 0,
        "advance_decline_ratio": 0,
        "advancing_volume_pct": 0,
        "stocks_near_52w_high": 0,
        "stocks_near_52w_low": 0,
        "high_low_ratio": 0,
        "above_20_day_ma_pct": 0,
        "above_50_day_ma_pct": 0,
        "above_200_day_ma_pct": 0
      },
      "index_table_3day": {
        "dates": ["YYYY-MM-DD", "YYYY-MM-DD", "YYYY-MM-DD"],
        "rows": [
          {
            "symbol": "^GSPC",
            "name": "S&P 500",
            "values": [
              { "date": "YYYY-MM-DD", "close": 0, "daily_return_percent": 0 },
              { "date": "YYYY-MM-DD", "close": 0, "daily_return_percent": 0 },
              { "date": "YYYY-MM-DD", "close": 0, "daily_return_percent": 0 }
            ]
          }
        ],
        "source": "major-indexes/us_major_indices_historical.json"
      },
      "vix_table": {
        "dates": ["YYYY-MM-DD", "YYYY-MM-DD", "YYYY-MM-DD"],
        "symbol": "^VIX",
        "name": "CBOE Volatility Index",
        "values": [
          { "date": "YYYY-MM-DD", "close": 0, "daily_return_percent": 0 }
        ],
        "source": "major-indexes/us_major_indices_historical.json"
      },
      "major_indexes_table": [
        { "symbol": "^GSPC", "name": "S&P 500", "close": 0, "change": 0, "change_percent": 0 }
      ],
      "sector_leaders": [
        { "symbol": "XLK", "sector_name": "Technology", "close": 0, "change_percent": 0 }
      ],
      "sector_laggards": [
        { "symbol": "XLU", "sector_name": "Utilities", "close": 0, "change_percent": 0 }
      ],
      "volatility_summary": {
        "vix": { "symbol": "^VIX", "close": 0, "change": 0, "change_percent": 0 },
        "major_index_iv": [
          { "symbol": "SPY", "average_iv": 0, "average_iv_formatted": "0%", "iv_level": "Normal" }
        ]
      },
      "technical_levels": {
        "SPY": {
          "reference_date": "YYYY-MM-DD",
          "traditional_pivots": { "P": 0, "R1": 0, "R2": 0, "S1": 0, "S2": 0 },
          "fibonacci_pivots": { "FP": 0, "FR1": 0, "FR2": 0, "FS1": 0, "FS2": 0 },
          "sma": { "SMA20": 0, "SMA50": 0, "SMA200": 0 }
        }
      }
    }
  }
}
```

## Usage Examples

### Fetch from R2 (Recommended)

```javascript
// Fastest access via Cloudflare R2
const url = 'https://r2.deanfi.com/dailycombined/market_snapshot.json';
const response = await fetch(url);
const snapshot = await response.json();

// Access specific data
console.log('Market Breadth:', snapshot.data.market_breadth);
console.log('S&P 500:', snapshot.data.major_indexes.us_major['^GSPC']);
console.log('Top News:', snapshot.data.news.top_news);
```

### Fetch from GitHub Raw

```javascript
// Alternative via GitHub (with caching)
const url = 'https://raw.githubusercontent.com/DeanFinancials/deanfi-data/main/dailycombined/market_snapshot.json';
const response = await fetch(url);
const snapshot = await response.json();
```

### Python Example

```python
import requests

# Fetch combined snapshot
url = 'https://r2.deanfi.com/dailycombined/market_snapshot.json'
response = requests.get(url)
snapshot = response.json()

# Access data
market_breadth = snapshot['data']['market_breadth']
sp500 = snapshot['data']['major_indexes']['us_major']['SPY']

print(f"S&P 500 Advances: {market_breadth['advances_declines']['advances']}")
print(f"S&P 500 Price: ${sp500['price']}")
```

## Benefits

### For Developers
- **Single API Call:** Get all daily market data in one request
- **Reduced Latency:** One file = one network round-trip
- **Simpler Code:** No need to orchestrate multiple fetches
- **Consistent Structure:** Predictable JSON schema

### For Applications
- **Faster Page Loads:** Fewer HTTP requests
- **Lower Bandwidth:** Combined data is more efficient than separate files
- **Better UX:** All data arrives together, no loading waterfalls
- **Edge Caching:** Single file is easier to cache at CDN edge

## File Size

Typical file size: **~800 KB–1.4 MB** (uncompressed JSON)

With gzip compression (automatic with most CDNs): typically **~150–350 KB**

## Automation

### Generation Script
- **Location:** `dailycombined/combine_daily_snapshots.py`
- **Language:** Python 3.11+
- **Dependencies:** None (uses only standard library)

### GitHub Actions Workflow
- **Location:** `.github/workflows/combine-daily-snapshots.yml`
- **Schedule:** `38 21 * * 1-5` (4:38pm ET, weekdays only)
- **Runtime:** ~5-10 seconds
- **Deployment:** Directly uploads to R2 bucket at `dailycombined/market_snapshot.json`
- **Optional:** Also commits to repository (with `continue-on-error: true`)

## Data Freshness

Each data source includes its own `last_updated` timestamp in the metadata. The combined snapshot's `generated_at` timestamp shows when the combination was performed.

**Typical Update Times (ET):**
- Economy indicators: 8:00am, 12:00pm
- Daily news: 9:30am, 4:00pm
- Market data (15-min updates): 9:03am - 4:33pm
- **Combined snapshot:** 4:38pm (all daily data included)

## Error Handling

The combination script is resilient:
- **Missing files:** Skips missing data sources without failing
- **Malformed JSON:** Logs error and continues with other sources
- **Partial data:** Generates snapshot with whatever data is available

The metadata shows exactly which sources were successfully included.

## Related Files

- **Individual Snapshots:** See respective directories for detailed documentation
  - `advance-decline/README.md`
  - `major-indexes/README.md`
  - `meanreversion/README.md`
  - `implied-volatility/README.md`
  - `daily-news/README.md`
  - `economy-breadth/README.md`

- **Historical Data:** For time-series analysis, use the `*_historical.json` files in respective directories

## Support

For issues, questions, or feature requests:
- GitHub Issues: https://github.com/DeanFinancials/deanfi-data/issues
- Discussions: https://github.com/orgs/DeanFinancials/discussions

## License

MIT License - See LICENSE file in repository root
