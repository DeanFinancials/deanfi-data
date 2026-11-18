# Developer Requirements - deanfi-data

## Overview

This repository serves as a centralized data store for financial market data collected by [deanfi-collectors](https://github.com/DeanFinancials/deanfi-collectors). Data is stored in JSON format and synced to Cloudflare R2 for high-performance edge access.

## Repository Purpose

- **Primary Function**: Store market data JSON files updated by automated collectors
- **Secondary Function**: Sync data to Cloudflare R2 bucket for CDN access
- **Consumers**: deanfi-website and other client applications

## Data Pipeline Architecture

```
┌─────────────────┐
│ deanfi-collectors│  ← Python scripts running on GitHub Actions
│  (Automated)     │     Every 15 min (market hours) or daily/weekly
└────────┬─────────┘
         │ git commit & push (only changed files)
         ▼
┌──────────────────┐
│   deanfi-data    │  ← This repository (JSON storage)
│  (Git Storage)   │
└────────┬─────────┘
         │ GitHub Action: sync-to-r2.yml
         │ Uploads only changed *.json files
         ▼
┌──────────────────┐
│  Cloudflare R2   │  ← Cloud object storage
│  (CDN Storage)   │     Public bucket: deanfi-data
└────────┬─────────┘
         │ Direct fetch or custom domain
         ▼
┌──────────────────┐
│  deanfi-website  │  ← Astro website (SSG/SSR)
│  & API Consumers │     Fetches from R2 at build/runtime
└──────────────────┘
```

## Directory Structure

```
deanfi-data/
├── .github/
│   └── workflows/
│       └── sync-to-r2.yml          # Auto-sync changed files to R2
├── advance-decline/
│   ├── ad_line_historical.json
│   ├── daily_breadth.json
│   ├── highs_lows_historical.json
│   └── ma_percentage_historical.json
├── analyst-trends/
│   ├── recommendation_trends.json
│   └── sector_recommendation_trends.json
├── cache/                           # Metadata cache for collectors
├── daily-news/
│   ├── sector_news.json
│   └── top_news.json
├── earnings-calendar/
│   └── earnings_calendar.json
├── earnings-surprises/
│   └── earnings_surprises.json
├── economy-breadth/
│   ├── growth_output.json
│   ├── inflation_prices.json
│   ├── labor_employment.json
│   └── money_markets.json
├── implied-volatility/
│   ├── major_indices_iv_snapshot.json
│   ├── sector_etfs_iv_snapshot.json
│   └── vix_options_snapshot.json
├── major-indexes/
│   ├── bond_treasury_indices.json
│   ├── bond_treasury_indices_historical.json
│   ├── commodity_indices.json
│   ├── commodity_indices_historical.json
│   ├── international_major_indices.json
│   ├── international_major_indices_historical.json
│   ├── us_growth_value_indices.json
│   ├── us_growth_value_indices_historical.json
│   ├── us_major_indices.json
│   ├── us_major_indices_historical.json
│   ├── us_sector_indices.json
│   └── us_sector_indices_historical.json
├── metadata.json                    # Global metadata
├── LICENSE
└── README.md
```

## Data Format Standards

All JSON files follow a consistent structure:

```json
{
  "metadata": {
    "generated_at": "ISO 8601 timestamp",
    "source": "Data source name",
    "total_records": 0,
    "...additional metadata..."
  },
  "data": [
    // Array of data records
  ]
}
```

## GitHub Actions Workflows

### sync-to-r2.yml

**Trigger**: On push to `main` branch when `*.json` files change (no schedule; `combine-daily-snapshots.yml` uploads its own outputs)  
**Purpose**: Upload the JSON files changed across the whole push (`before..sha`) to Cloudflare R2 bucket  
**Concurrency**: Single sync at a time to prevent conflicts

**Required Secrets** (Organization or Repository level):
- `CLOUDFLARE_ACCOUNT_ID` - Cloudflare account ID
- `CLOUDFLARE_API_TOKEN` - API token with R2 write permissions
- `R2_BUCKET_NAME` - Target R2 bucket name (e.g., `deanfi-data`)

**Environment Variables**:
- None (all configuration via secrets)

## Cloudflare R2 Configuration

### Bucket Setup

- **Bucket Name**: `deanfi-data`
- **Public Access**: Enabled (for direct fetching)
- **CORS Policy**: Allow all origins for JSON files
- **Custom Domain**: (Optional) `data.deanfinancials.com`

### R2 API Token Permissions

Required permissions for the API token:
- Account: `R2 Read & Write`
- Scope: Specific bucket (`deanfi-data`)

## Data Access Patterns

### Option 1: Direct R2 Public URL
```javascript
const response = await fetch('https://pub-xxxxx.r2.dev/daily-news/top_news.json');
const data = await response.json();
```

### Option 2: Custom Domain (Recommended)
```javascript
const response = await fetch('https://data.deanfinancials.com/daily-news/top_news.json');
const data = await response.json();
```

### Option 3: Via GitHub Raw (Legacy)
```javascript
const response = await fetch('https://raw.githubusercontent.com/DeanFinancials/deanfi-data/main/daily-news/top_news.json');
const data = await response.json();
```

## Best Practices

### For AI Assistants

1. **Never modify data files directly** - Only deanfi-collectors should update JSON files
2. **Always update README.md** when adding new data sources or endpoints
3. **Maintain metadata consistency** across all JSON files
4. **Document new workflows** in this file and CHANGELOG_AND_IMPLEMENTATION_LOG.md
5. **Test R2 sync** after modifying sync-to-r2.yml workflow

### For Manual Updates

1. Only update documentation files (README.md, this file, etc.)
2. Do not manually edit JSON files - let collectors handle it
3. Verify R2 sync succeeded after pushing changes
4. Check Cloudflare R2 dashboard for upload confirmation

## Monitoring & Debugging

### Verify R2 Sync Status

1. Check GitHub Actions tab for `sync-to-r2.yml` workflow runs
2. Review workflow logs for upload confirmation
3. Check Cloudflare R2 dashboard for file timestamps
4. Test data access via public URL or custom domain

### Common Issues

**Issue**: R2 sync fails with authentication error  
**Solution**: Verify `CLOUDFLARE_ACCOUNT_ID` and `CLOUDFLARE_API_TOKEN` secrets are set correctly

**Issue**: Some files not syncing to R2  
**Solution**: Check if files actually changed in the commit (Git only syncs modified files)

**Issue**: R2 bucket not accessible publicly  
**Solution**: Enable public access in R2 bucket settings

## External Documentation

- [Cloudflare R2 Documentation](https://developers.cloudflare.com/r2/)
- [Cloudflare R2 API Reference](https://developers.cloudflare.com/api/operations/r2-get-bucket)
- [Wrangler CLI Documentation](https://developers.cloudflare.com/workers/wrangler/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions)

## Version History

- **v1.0.0** (2025-11-22): Initial documentation with R2 sync implementation
