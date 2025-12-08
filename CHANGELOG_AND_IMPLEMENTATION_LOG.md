# Changelog and Implementation Log - deanfi-data

## Overview

This document tracks all implementations, changes, and updates to the deanfi-data repository.

---

## [2025-12-08] - SP500 Growth Data Added

### Added

#### New Dataset: sp500growth/
- **sp500growth.json**: Growth metrics for all S&P 500 companies (~500 tickers)
- **README.md**: Documentation for the new dataset

### Background
The deanfi-collectors repository now includes a unified S&P growth collector that generates both sp100growth.json and sp500growth.json from a single run. This eliminates duplicate API calls since S&P 100 companies are already included in the S&P 500.

### Data Format
The sp500growth.json uses the same format as sp100growth.json:
- `_README`: Self-documenting schema
- `metadata`: Generation timestamp, ticker counts, universe name
- `companies`: Growth metrics keyed by ticker symbol

### Access
```
https://r2.deanfi.com/sp500growth/sp500growth.json
```

---

## [2025-11-26] - R2 Domain Migration

### Changed

#### R2 URL Migration
- **Migration**: Updated all R2 URLs from `r2.deanfinancials.com` to `r2.deanfi.com` to align with primary domain change
- **Reason**: Primary domain migrated from deanfinancials.com to deanfi.com with page rule redirect. Old R2 subdomain now redirects, breaking data fetching.

**Files Updated**:
1. `.github/workflows/combine-daily-snapshots.yml` - Updated success message URL
2. `dailycombined/README.md` - Updated JavaScript and Python example URLs (2 occurrences)
3. `README.md` - Updated quick start examples for combined snapshot and individual datasets (2 occurrences)

**Impact**:
- All documentation now references correct R2 endpoint
- GitHub Actions workflow outputs correct URL
- Example code in READMEs works with current infrastructure

---

## [2025-11-22] - Cloudflare R2 Integration & Documentation

### Added

#### 1. Documentation Files
- **DEVELOPER_REQUIREMENTS.md**: Complete developer guide covering:
  - Repository purpose and architecture
  - Data pipeline flow from collectors → Git → R2 → consumers
  - Directory structure and data format standards
  - GitHub Actions workflow configuration
  - Cloudflare R2 setup and access patterns
  - Best practices and troubleshooting guide

- **CHANGELOG_AND_IMPLEMENTATION_LOG.md** (this file): Implementation tracking

#### 2. GitHub Actions Workflow

**File**: `.github/workflows/sync-to-r2.yml`

**Purpose**: Automatically sync only changed JSON files to Cloudflare R2 bucket

**Features**:
- Triggers on push to `main` branch when `*.json` files change
- Detects which files actually changed using `git diff`
- Uploads only modified files to R2 (not entire directory)
- Uses Wrangler CLI for R2 uploads
- Includes error handling and upload verification
- Concurrent workflow protection to prevent conflicts

**Required GitHub Secrets** (Organization or Repository level):
1. `CLOUDFLARE_ACCOUNT_ID` - Your Cloudflare account ID
2. `CLOUDFLARE_API_TOKEN` - API token with R2 read/write permissions
3. `R2_BUCKET_NAME` - Name of your R2 bucket (e.g., `deanfi-data`)

**Workflow Steps**:
1. Checkout repository with 2-commit history for diff
2. Detect changed JSON files using `git diff --name-only HEAD^ HEAD`
3. Install Wrangler CLI globally
4. Upload each changed file to R2 bucket using `wrangler r2 object put`
5. Report upload status (success or failure)

**Configuration**:
```yaml
env:
  R2_BUCKET_NAME: deanfi-data  # Change if using different bucket name
```

#### 3. README.md Updates

**Section Added**: "Cloudflare R2 Access"
- Documented R2 public URL access pattern
- Provided custom domain setup guidance
- Included example code for fetching from R2
- Added performance benefits vs GitHub raw URLs

**Section Updated**: "Quick Start"
- Added R2 as preferred data source
- Maintained GitHub raw URL examples for backward compatibility
- Documented caching strategies for R2 access

### Implementation Details

#### Architecture Decision: Git-First Approach

**Why Git remains primary storage**:
1. Version control and audit trail
2. Easy rollback and history tracking
3. Existing collector workflows unchanged
4. R2 serves as CDN/cache layer, not source of truth

**Data Flow**:
```
Collectors (Python) 
  → Git commit (only changed files)
  → GitHub Action detects changes
  → Uploads changed files to R2
  → Consumers fetch from R2
```

#### Performance Benefits

**R2 vs GitHub Raw URLs**:
- **Latency**: R2 ~50ms vs GitHub Raw ~200-500ms (global edge network)
- **Throughput**: R2 has no rate limits vs GitHub's 5000 req/hour for authenticated
- **Cost**: R2 free egress to Cloudflare services vs potential GitHub API limits
- **Caching**: R2 built-in edge caching vs manual cache implementation

#### Selective Upload Strategy

**Git Diff Approach**:
```bash
git diff --name-only HEAD^ HEAD | grep '\.json$'
```

**Benefits**:
- Only uploads files that actually changed in the commit
- Reduces upload time (important for 15-min update frequency)
- Minimizes R2 write operations
- Prevents unnecessary object versioning

**Edge Cases Handled**:
- No files changed: Workflow exits gracefully
- Multiple files changed: Loops through all changed files
- Upload failure: Reports error but continues with remaining files

### Configuration Guide

#### Step 1: Create Cloudflare R2 Bucket

1. Log into Cloudflare Dashboard
2. Navigate to **R2 Object Storage**
3. Click **Create bucket**
4. Bucket name: `deanfi-data`
5. Enable **Public access** (for direct fetching)

#### Step 2: Generate API Token

1. Navigate to **My Profile** → **API Tokens**
2. Click **Create Token**
3. Select **Create Custom Token**
4. Permissions:
   - Account: `R2 Read & Write`
   - Zone Resources: Not needed
5. Continue to summary
4. Repository access: Select `deanfi-data` or all repos

#### Step 3: Configure GitHub Secrets

**For Organization Secrets** (recommended):
1. Navigate to Organization Settings → Secrets and variables → Actions
2. Click **New organization secret**
3. Add three secrets:
   - Name: `CLOUDFLARE_ACCOUNT_ID`
     Value: Your account ID (found in R2 dashboard URL)
   - Name: `CLOUDFLARE_API_TOKEN`
     Value: API token from Step 2
   - Name: `R2_BUCKET_NAME`
     Value: Your bucket name (e.g., `deanfi-data`)
4. Repository access: Select `deanfi-data` or all repos

**For Repository Secrets** (alternative):
1. Navigate to Repository Settings → Secrets and variables → Actions
2. Add the same three secrets as above

#### Step 4: Enable Public Access (Optional)

1. In R2 bucket settings, go to **Settings** tab
2. Under **Public access**, click **Allow Access**
3. Note the public URL: `https://pub-xxxxx.r2.dev`

#### Step 5: Configure Custom Domain (Optional)

1. In R2 bucket settings, go to **Settings** tab
2. Under **Custom Domains**, click **Connect Domain**
3. Enter domain: `data.deanfinancials.com`
4. Add DNS CNAME record as instructed
5. Wait for DNS propagation (up to 24 hours)

### Testing

#### Test Workflow Locally

Not possible - R2 uploads require Cloudflare API, must test via GitHub Actions.

#### Test Workflow on GitHub

1. Make a minor change to any JSON file (add a space)
2. Commit and push to `main` branch
3. Navigate to **Actions** tab
4. Watch `Sync to Cloudflare R2` workflow run
5. Verify upload success in logs
6. Check R2 bucket dashboard for updated file timestamp

#### Verify R2 Access

```bash
# Test public access (replace with your bucket URL)
curl https://pub-xxxxx.r2.dev/daily-news/top_news.json

# Test custom domain (if configured)
curl https://data.deanfinancials.com/daily-news/top_news.json

# Verify JSON structure
curl https://pub-xxxxx.r2.dev/daily-news/top_news.json | jq '.metadata'
```

### Known Limitations

1. **Git history required**: Workflow needs at least 2 commits to detect changes
   - **Impact**: Initial repository setup may need manual upload
   - **Workaround**: Run workflow manually with `workflow_dispatch` for first upload

2. **Large files**: Git has 100MB file limit
   - **Impact**: Historical data files must stay under 100MB
   - **Mitigation**: Archive old data or use pagination

3. **Sync delay**: ~30-60 seconds from commit to R2 availability

## Issue Resolution Log

### 2025-11-23: Local vs Remote R2 Upload Issue

**Problem**: Initial workflow run appeared successful (26/26 files uploaded) but files were not visible in R2 bucket dashboard or accessible via API.

**Root Cause**: Wrangler 4.50.0+ defaults to **local mode** for R2 operations. Workflow logs showed `Resource location: local` despite `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` environment variables being set correctly. Files were uploaded to GitHub Actions runner's local storage instead of Cloudflare R2.

**Solution**: Added `--remote` flag to wrangler command:
```bash
wrangler r2 object put "$R2_BUCKET_NAME/$file" --file="$file" --remote
```

**Verification**: After fix, workflow logs should display:
```
Resource location: remote
```
Instead of `Resource location: local`

**Impact**: All previous uploads to R2 need to be re-run after workflow update.
   - **Impact**: Brief window where Git and R2 are out of sync
   - **Mitigation**: Consumers should implement graceful fallback to GitHub raw URLs

### 2025-11-22: Authentication Clarification & Workflow Validation Step

**Problem**: Continued `403 Forbidden` and Authentication error `10000` responses when using `wrangler r2 object put` despite adding `--remote` flag. Attempts used R2 S3-style Access Keys (Access Key ID / Secret Access Key) in place of Cloudflare API Tokens.

**Root Cause**: Wrangler `r2` subcommands (e.g., `wrangler r2 object put`, `wrangler r2 bucket list`) authenticate via Cloudflare API Tokens (OAuth or API Token with appropriate scopes), not via R2 S3 access keys. The S3 access keys only work against the S3-compatible endpoint (`https://<ACCOUNT_ID>.r2.cloudflarestorage.com`) using S3 clients. Passing the R2 Secret Access Key as `CLOUDFLARE_API_TOKEN` results in failed authorization.

**Resolution**:
1. Create a Cloudflare API Token (Dashboard → My Profile → API Tokens → Create Custom Token).
2. Assign permissions: `Account R2 Storage:Edit` (grants read & write) – least privilege sufficient for bucket/object operations.
3. Store token as `CLOUDFLARE_API_TOKEN` secret; keep `CLOUDFLARE_ACCOUNT_ID` and `R2_BUCKET_NAME` unchanged.
4. Added new workflow step `Verify Cloudflare authentication & bucket access` executing `wrangler whoami` and `wrangler r2 bucket list --remote` before uploads.
5. Strengthened upload step with `set -euo pipefail` and added bucket info diagnostic on first failure.

**Workflow File Updated**: `.github/workflows/sync-to-r2.yml`
**Change Summary**:
- Added pre-upload auth validation step.
- Added explanatory note differentiating API Tokens vs R2 S3 access keys.
- Early failure with clear messaging if bucket not visible or token invalid.
- Added diagnostic bucket info fetch on first object upload failure.

**Impact**:
- Prevents misleading "successful" local-mode uploads with wrong credentials.
- Speeds troubleshooting by surfacing misconfiguration before looped uploads.

**Verification Instructions**:
Run manual dispatch of workflow; confirm log contains:
```
✅ Wrangler whoami succeeded. Listing buckets...
✅ Bucket 'deanfi-data' accessible. Proceeding with uploads.
```
Followed by remote upload successes.

**Future Consideration**: Optionally rename secret to `CLOUDFLARE_R2_API_TOKEN` for clarity, but deferred to avoid churn.

**References Used**:
- Cloudflare Docs (Wrangler Commands & Configuration – last updated Nov 10, 2025)
- R2 Workers API vs S3 API distinction.


### Future Enhancements

**Planned**:
- [ ] Add R2 bucket versioning for rollback capability
- [ ] Implement webhook notification on successful sync
- [ ] Add monitoring/alerting for sync failures
- [ ] Create daily sync verification job
- [ ] Add support for deleting removed files from R2

**Under Consideration**:
- [ ] Compress JSON files with gzip for smaller storage
- [ ] Add checksum validation before/after upload
- [ ] Implement incremental backup to R2 archive bucket
- [ ] Create CLI tool for manual R2 sync operations

### References

**Documentation Created**:
- DEVELOPER_REQUIREMENTS.md - Complete developer guide
- .github/workflows/sync-to-r2.yml - R2 sync automation
- Updated README.md with R2 access patterns

**External Documentation Used**:
- [Cloudflare R2 Documentation](https://developers.cloudflare.com/r2/)
- [Wrangler CLI - R2 Commands](https://developers.cloudflare.com/workers/wrangler/commands/#r2)
- [GitHub Actions - Workflow Syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [GitHub Actions - Using Secrets](https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions)

### Contributors

- GitHub Copilot (AI) - Initial implementation and documentation
- User request - R2 integration specification

---

## [Pre-2025-11-22] - Repository Initialization

### Existing Structure

**Data Categories** (managed by deanfi-collectors):
- `advance-decline/` - Market breadth metrics
- `analyst-trends/` - Recommendation trends
- `daily-news/` - News articles
- `earnings-calendar/` - Upcoming earnings
- `earnings-surprises/` - Historical earnings surprises
- `economy-breadth/` - Economic indicators
- `implied-volatility/` - Options volatility data
- `major-indexes/` - Index pricing and historical data
- `cache/` - Collector metadata cache

**Update Frequencies**:
- Every 15 minutes (market hours): Market breadth, indexes, implied volatility
- Twice daily: Daily news, sector news
- Weekly: Analyst trends, earnings data

**Automation**:
- Updated by [deanfi-collectors](https://github.com/DeanFinancials/deanfi-collectors)
- GitHub Actions workflows push data every 15 minutes
- Concurrency control prevents write conflicts

### Initial Files

- README.md - User-facing documentation with data formats and examples
- LICENSE - MIT license
- metadata.json - Global repository metadata
- All JSON data files in respective directories

---

## Maintenance Notes

### When Adding New Data Sources

1. Update DEVELOPER_REQUIREMENTS.md with new directory structure
2. Update README.md with new endpoints and examples
3. Document in this changelog under new version
4. Verify R2 sync picks up new files automatically
5. Test access via R2 public URL

### When Modifying Workflows

1. Test changes in a fork or branch first
2. Document changes in DEVELOPER_REQUIREMENTS.md
3. Update this changelog with implementation details
4. Monitor first production run closely
5. Update troubleshooting guide if new issues arise

### When Updating Documentation

1. Keep README.md user-focused (how to use the data)
2. Keep DEVELOPER_REQUIREMENTS.md technical (how it works)
3. Keep this file historical (what changed and why)
4. Cross-reference between documents
5. Update version numbers and dates
