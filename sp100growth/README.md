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
