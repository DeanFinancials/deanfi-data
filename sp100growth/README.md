# SP100 Growth Data

S&P 100 company growth metrics extracted from SEC EDGAR filings.

## Files

| File | Description | Update Frequency |
|------|-------------|------------------|
| `sp100growth.json` | Growth metrics for all S&P 100 companies | Nightly (11:15pm ET) |

## Data Format

```json
{
  "_README": { ... },
  "metadata": {
    "generated_at": "2025-12-06T04:15:00Z",
    "data_source": "SEC EDGAR + Finnhub",
    "ticker_count": 100,
    "successful_extractions": 98,
    "universe": "S&P 100"
  },
  "companies": {
    "AAPL": {
      "ticker": "AAPL",
      "company_name": "Apple Inc.",
      "annual_values": {
        "2024": {"revenue": 391035000000, "eps": 6.08},
        "2023": {"revenue": 383285000000, "eps": 6.13},
        "2022": {"revenue": 394328000000, "eps": 6.11}
      },
      "quarterly_values": {
        "2024-Q3": {"revenue": 94930000000, "eps": 1.40},
        "2024-Q2": {"revenue": 85777000000, "eps": 1.53},
        "2024-Q1": {"revenue": 90753000000, "eps": 1.53}
      },
      "growth": {
        "revenue_yoy": {"2024": -0.028, "2023": 0.078},
        "eps_yoy": {"2024": -0.003, "2023": 0.041},
        "ttm": {
          "revenue": 383285000000,
          "eps_diluted": 6.11,
          "revenue_yoy": 0.02,
          "eps_yoy": 0.05
        },
        "revenue_cagr_3yr": 0.024,
        "eps_cagr_3yr": 0.019
      }
    }
  }
}
```

## Metrics

| Metric | Description |
|--------|-------------|
| `annual_values` | Actual annual revenue and EPS by year |
| `annual_values[year].revenue` | Annual revenue (USD) |
| `annual_values[year].eps` | Annual diluted EPS (USD per share) |
| `quarterly_values` | Actual quarterly revenue and EPS by quarter |
| `quarterly_values[qtr].revenue` | Quarterly revenue (USD) |
| `quarterly_values[qtr].eps` | Quarterly diluted EPS (USD per share) |
| `revenue_yoy` | Year-over-year revenue growth (decimal) |
| `eps_yoy` | Year-over-year EPS growth (decimal) |
| `ttm.revenue` | Trailing 12 months revenue (USD) |
| `ttm.eps_diluted` | Trailing 12 months diluted EPS |
| `ttm.revenue_yoy` | TTM revenue growth vs prior TTM |
| `ttm.eps_yoy` | TTM EPS growth vs prior TTM |
| `revenue_cagr_3yr` | 3-year revenue CAGR |
| `eps_cagr_3yr` | 3-year EPS CAGR |
| `revenue_cagr_5yr` | 5-year revenue CAGR |
| `eps_cagr_5yr` | 5-year EPS CAGR |

## Data Sources

- **Primary**: SEC EDGAR (10-K and 10-Q filings)
- **Fallback**: Finnhub API (for quarterly data when SEC is incomplete)

## Usage

```javascript
// Fetch from R2 CDN
const url = 'https://r2.deanfi.com/sp100growth/sp100growth.json';
const response = await fetch(url);
const data = await response.json();

// Get Apple's growth metrics
console.log(data.companies.AAPL.growth);

// Filter companies with >10% revenue growth
const highGrowth = Object.values(data.companies).filter(
  c => c.growth.ttm?.revenue_yoy > 0.10
);
```

## Notes

- All growth rates are decimals (multiply by 100 for percentage)
- Null values indicate insufficient data
- Revenue figures are in USD (not scaled)
- Fiscal year end dates vary by company
