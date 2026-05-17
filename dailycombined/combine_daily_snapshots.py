#!/usr/bin/env python3
"""
Combine Daily Market Snapshots

This script combines all daily snapshot data from various collectors into a single
comprehensive market snapshot JSON file for easy consumption by client applications.

Daily Snapshot Sources:
- advance-decline/daily_breadth.json - Market breadth indicators
- major-indexes/*.json (snapshot versions) - Major market indices
- meanreversion/*_snapshot.json - Mean reversion metrics
- supportresistence/support_resistence.json - Pivot points + SMAs (support/resistence)
- implied-volatility/*_snapshot.json - Implied volatility data
- daily-news/*.json - Market news
- economy-breadth/*.json - Economic indicators

Output: market_snapshot.json - Combined snapshot with all daily data
"""
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional


def is_empty_value(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, (list, tuple, set)):
        return len(value) == 0
    if isinstance(value, dict):
        return len(value) == 0
    return False


def set_block_status(
    combined: Dict[str, Any],
    block: str,
    *,
    status: str,
    reason: Optional[str] = None,
    source: Optional[str] = None,
    last_updated: Optional[str] = None,
    record_count: Optional[int] = None,
) -> None:
    blocks = combined.setdefault('metadata', {}).setdefault('blocks', {})
    payload: Dict[str, Any] = {'status': status}
    if reason:
        payload['reason'] = reason
    if source:
        payload['source'] = source
    if last_updated:
        payload['last_updated'] = last_updated
    if record_count is not None:
        payload['record_count'] = record_count
    blocks[block] = payload


def load_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load a JSON file and return its contents.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Dictionary with JSON contents or None if file doesn't exist/fails to load
    """
    try:
        if file_path.exists():
            with open(file_path, 'r') as f:
                return json.load(f)
        else:
            print(f"⚠️  File not found: {file_path}")
            return None
    except Exception as e:
        print(f"❌ Error loading {file_path}: {e}")
        return None


def pick_first_present(payload: Dict[str, Any], keys: list[str], default: Any) -> Any:
    for key in keys:
        if key in payload and not is_empty_value(payload.get(key)):
            return payload.get(key)
    return default


def derive_previous_market_date(data_dir: Path, market_date: str) -> Optional[str]:
    """Derive the previous trading date from existing historical datasets.

    This avoids adding calendar dependencies while still providing a stable,
    writer-friendly `previous_market_date` field in the combined snapshot.
    """
    if not market_date or not isinstance(market_date, str):
        return None

    candidate_files = [
        data_dir / 'advance-decline' / 'ma_percentage_historical.json',
        data_dir / 'advance-decline' / 'highs_lows_historical.json',
        data_dir / 'advance-decline' / 'ad_line_historical.json',
    ]

    for file_path in candidate_files:
        payload = load_json_file(file_path)
        if not payload:
            continue
        series = payload.get('data')
        if not isinstance(series, list) or not series:
            continue

        dates: list[str] = []
        for row in series:
            if not isinstance(row, dict):
                continue
            value = row.get('date')
            if isinstance(value, str) and value:
                dates.append(value)

        if not dates:
            continue

        unique_dates = sorted(set(dates))
        prev_dates = [d for d in unique_dates if d < market_date]
        if prev_dates:
            return prev_dates[-1]

    return None


def get_last_trading_dates_from_us_major_history(
    data_dir: Path,
    market_date: str,
    *,
    count: int,
) -> list[str]:
    """Return up to `count` trading dates ending at `market_date`.

    Uses `major-indexes/us_major_indices_historical.json` (the most reliable
    canonical trading-day series we have locally) and the ^GSPC date series.
    """
    if count <= 0:
        return []
    if not market_date or not isinstance(market_date, str):
        return []

    history = load_json_file(data_dir / 'major-indexes' / 'us_major_indices_historical.json')
    if not history:
        return []
    indices = history.get('indices')
    if not isinstance(indices, dict):
        return []
    gspc = indices.get('^GSPC')
    if not isinstance(gspc, dict):
        return []
    series = gspc.get('data')
    if not isinstance(series, list) or not series:
        return []

    dates = [row.get('date') for row in series if isinstance(row, dict) and isinstance(row.get('date'), str)]
    dates = sorted(set(dates))
    if not dates:
        return []

    # Find exact match; otherwise pick the last date <= market_date.
    if market_date in dates:
        end_idx = dates.index(market_date)
    else:
        earlier = [d for d in dates if d <= market_date]
        if not earlier:
            return []
        end_idx = dates.index(earlier[-1])

    start_idx = max(0, end_idx - (count - 1))
    return dates[start_idx : end_idx + 1]


def build_close_return_lookup(history: Dict[str, Any], symbol: str) -> Dict[str, Dict[str, Any]]:
    indices = history.get('indices') if isinstance(history, dict) else None
    if not isinstance(indices, dict):
        return {}
    item = indices.get(symbol)
    if not isinstance(item, dict):
        return {}
    series = item.get('data')
    if not isinstance(series, list):
        return {}

    lookup: Dict[str, Dict[str, Any]] = {}
    for row in series:
        if not isinstance(row, dict):
            continue
        date = row.get('date')
        if not isinstance(date, str) or not date:
            continue
        lookup[date] = {
            'close': row.get('close'),
            'daily_return_percent': row.get('daily_return_percent'),
        }
    return lookup


def build_simple_date_lookup(series_payload: Optional[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Build a date->row lookup for common deanfi-data historical series."""
    if not isinstance(series_payload, dict):
        return {}
    data = series_payload.get('data')
    if not isinstance(data, list):
        return {}
    out: Dict[str, Dict[str, Any]] = {}
    for row in data:
        if not isinstance(row, dict):
            continue
        date = row.get('date')
        if isinstance(date, str) and date:
            out[date] = row
    return out


def parse_iso_datetime(value: Any) -> Optional[datetime]:
    if not isinstance(value, str) or not value:
        return None
    normalized = value.replace('Z', '+00:00')
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def is_stale_for_market_date(last_updated: Any, market_date: Optional[str]) -> bool:
    if not market_date:
        return False
    parsed = parse_iso_datetime(last_updated)
    if not parsed:
        return False
    return parsed.date().isoformat() < market_date


def has_meaningful_fund_flow_signal(fund_flows: Dict[str, Any]) -> bool:
    for payload in fund_flows.values():
        if not isinstance(payload, dict):
            continue
        daily_rows = ((payload.get('data') or {}).get('daily')) if isinstance(payload.get('data'), dict) else None
        if not isinstance(daily_rows, list):
            continue
        for row in daily_rows:
            groups = row.get('groups') if isinstance(row, dict) else None
            if not isinstance(groups, dict):
                continue
            for group in groups.values():
                if not isinstance(group, dict):
                    continue
                if group.get('flow_nav') is not None or group.get('flow_close') is not None:
                    return True
    return False


def get_whale_trade_count(payload: Dict[str, Any]) -> int:
    metadata = payload.get('metadata') if isinstance(payload.get('metadata'), dict) else {}
    value = metadata.get('total_whale_trades')
    return int(value) if isinstance(value, int) else 0


def build_optional_context(combined: Dict[str, Any]) -> Dict[str, Any]:
    metadata = combined.get('metadata', {}) if isinstance(combined.get('metadata'), dict) else {}
    blocks = metadata.get('blocks') if isinstance(metadata.get('blocks'), dict) else {}
    data = combined.get('data', {}) if isinstance(combined.get('data'), dict) else {}

    module_map = {
        'economy': 'economy',
        'earnings': 'weekly',
        'fund_flows': 'fund_flows',
        'options_whales': 'options_whales',
        'stock_whales': 'stock_whales',
    }

    out: Dict[str, Any] = {}
    for module_name, data_key in module_map.items():
        block = blocks.get(data_key) if isinstance(blocks.get(data_key), dict) else {}
        raw_status = block.get('status')
        module_data = data.get(data_key)

        if raw_status == 'ok' and not is_empty_value(module_data):
            status = 'included'
        elif raw_status == 'stale':
            status = 'omitted_stale'
        elif raw_status == 'low_relevance':
            status = 'omitted_low_relevance'
        else:
            status = 'omitted_empty'

        payload: Dict[str, Any] = {'status': status}
        for key in ['reason', 'source', 'last_updated', 'record_count']:
            if key in block:
                payload[key] = block[key]
        if status == 'included':
            payload['data'] = module_data
        out[module_name] = payload

    return out


REQUIRED_MARKET_PULSE_CORE_FIELDS = [
    'major_index_closes',
    'five_session_index_returns',
    'breadth',
    'five_session_breadth_lookback',
    'moving_average_participation',
    'sector_leaders',
    'sector_laggards',
    'vix',
    'five_session_vix_lookback',
    'major_etf_implied_volatility',
    'spy_technical_levels',
    'five_session_spy_sma',
]


def validate_market_pulse_core(core: Dict[str, Any]) -> Dict[str, Any]:
    failures = []
    field_status: Dict[str, str] = {}
    for field in REQUIRED_MARKET_PULSE_CORE_FIELDS:
        if is_empty_value(core.get(field)):
            failures.append(f'missing core.{field}')
            field_status[field] = 'missing'
        else:
            field_status[field] = 'present'

    return {
        'is_valid': not failures,
        'blocking_failures': failures,
        'core_fields': field_status,
    }


def build_market_pulse_input(combined: Dict[str, Any]) -> Dict[str, Any]:
    """Build the stricter Market Pulse article-generation package."""
    metadata = combined.get('metadata', {}) if isinstance(combined.get('metadata'), dict) else {}
    data = combined.get('data', {}) if isinstance(combined.get('data'), dict) else {}
    writer_ready = data.get('writer_ready') if isinstance(data.get('writer_ready'), dict) else {}
    breadth = writer_ready.get('breadth_table') if isinstance(writer_ready.get('breadth_table'), dict) else {}
    volatility = writer_ready.get('volatility_summary') if isinstance(writer_ready.get('volatility_summary'), dict) else {}
    technical_levels = writer_ready.get('technical_levels') if isinstance(writer_ready.get('technical_levels'), dict) else {}
    spy_levels = technical_levels.get('SPY') if isinstance(technical_levels.get('SPY'), dict) else {}

    core = {
        'major_index_closes': writer_ready.get('major_indexes_table') or [],
        'five_session_index_returns': writer_ready.get('index_table_5day') or {},
        'breadth': breadth,
        'five_session_breadth_lookback': writer_ready.get('breadth_lookback_5day') or {},
        'moving_average_participation': {
            'above_20_day_ma_pct': breadth.get('above_20_day_ma_pct'),
            'above_50_day_ma_pct': breadth.get('above_50_day_ma_pct'),
            'above_200_day_ma_pct': breadth.get('above_200_day_ma_pct'),
        },
        'sector_leaders': writer_ready.get('sector_leaders') or [],
        'sector_laggards': writer_ready.get('sector_laggards') or [],
        'vix': volatility.get('vix') if isinstance(volatility.get('vix'), dict) else {},
        'five_session_vix_lookback': writer_ready.get('vix_table_5day') or {},
        'major_etf_implied_volatility': volatility.get('major_index_iv') or [],
        'spy_technical_levels': spy_levels,
        'five_session_spy_sma': writer_ready.get('spy_sma_table_5day') or {},
    }
    validation = validate_market_pulse_core(core)
    pulse_input_status = 'ready' if validation['is_valid'] else 'partial'

    return {
        'metadata': {
            'market_date': metadata.get('market_date') or metadata.get('date'),
            'previous_market_date': metadata.get('previous_market_date'),
            'generated_at': metadata.get('generated_at'),
            'timezone': metadata.get('timezone') or 'America/New_York',
            'pulse_input_status': pulse_input_status,
            'data_sources': metadata.get('data_sources') or [],
        },
        'core': core,
        'catalysts': {
            'status': 'phase_2_pending',
            'ranked': [],
            'note': 'Catalyst collection and ranking are implemented in Phase 2; do not interpret an empty ranked list as no catalysts for the session.',
        },
        'optional_context': build_optional_context(combined),
        'validation': validation,
        'sources': {
            'snapshot': 'dailycombined/market_snapshot.json',
            'market_pulse_input': 'dailycombined/market_pulse_input.json',
            'schema': 'dailycombined/market_pulse_input.schema.json',
            'r2_url': 'https://r2.deanfi.com/dailycombined/market_pulse_input.json',
        },
    }


def write_combined_outputs(combined: Dict[str, Any], output_dir: Path) -> Dict[str, Path]:
    """Write the backward-compatible snapshot and the Market Pulse input."""
    snapshot_file = output_dir / 'market_snapshot.json'
    with open(snapshot_file, 'w') as f:
        json.dump(combined, f, indent=2)

    market_pulse_input = build_market_pulse_input(combined)
    market_pulse_file = output_dir / 'market_pulse_input.json'
    with open(market_pulse_file, 'w') as f:
        json.dump(market_pulse_input, f, indent=2)

    return {
        'market_snapshot': snapshot_file,
        'market_pulse_input': market_pulse_file,
    }


def combine_snapshots(data_dir: Path) -> Dict[str, Any]:
    """
    Combine all daily snapshot data into a single structure.
    
    Args:
        data_dir: Path to the deanfi-data directory
        
    Returns:
        Dictionary with combined snapshot data
    """
    session_market_date: Optional[str] = None
    combined = {
        'metadata': {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'description': 'Combined daily market snapshot from all data collectors',
            'data_sources': [],
            'update_schedule': 'Updated after market close (approximately 4:38pm ET on weekdays)',
            'blocks': {}
        },
        'data': {}
    }

    # Stable session metadata (additive / non-breaking)
    combined['metadata']['timezone'] = 'America/New_York'
    
    # ==================== MARKET BREADTH ====================
    print("\n📊 Loading market breadth data...")
    daily_breadth = load_json_file(data_dir / 'advance-decline' / 'daily_breadth.json')
    if daily_breadth:
        session_market_date = daily_breadth.get('data', {}).get('date') or session_market_date
        combined['data']['market_breadth'] = {
            'date': daily_breadth['data']['date'],
            'advances_declines': daily_breadth['data']['advances_declines'],
            'volume_metrics': daily_breadth['data']['volume_metrics'],
            'new_highs_lows': daily_breadth['data']['new_highs_lows'],
            'moving_averages': daily_breadth['data']['moving_averages']
        }
        combined['metadata']['data_sources'].append({
            'category': 'market_breadth',
            'source': 'advance-decline/daily_breadth.json',
            'last_updated': daily_breadth['metadata']['generated_at']
        })
        set_block_status(
            combined,
            'market_breadth',
            status='ok' if not is_empty_value(combined['data'].get('market_breadth')) else 'empty',
            source='advance-decline/daily_breadth.json',
            last_updated=daily_breadth.get('metadata', {}).get('generated_at'),
        )
        print("   ✓ Market breadth loaded")
    else:
        set_block_status(
            combined,
            'market_breadth',
            status='missing',
            reason='File missing or failed to load',
            source='advance-decline/daily_breadth.json',
        )
    
    # ==================== MAJOR INDEXES (Snapshot Versions) ====================
    print("\n📈 Loading major index snapshots...")
    indexes_data = {}
    
    index_files = {
        'us_major': 'us_major_indices.json',
        'us_sectors': 'us_sector_indices.json',
        'us_growth_value': 'us_growth_value_indices.json',
        'international': 'international_major_indices.json',
        'bonds': 'bond_treasury_indices.json',
        'commodities': 'commodity_indices.json'
    }
    
    for key, filename in index_files.items():
        index_data = load_json_file(data_dir / 'major-indexes' / filename)
        if index_data:
            # Support multiple upstream shapes:
            # - most major-indexes snapshots use `indices`
            # - sector snapshot uses `sectors`
            # - legacy/other datasets may use `data`
            indexes_data[key] = pick_first_present(index_data, ['data', 'indices', 'sectors'], {})
            combined['metadata']['data_sources'].append({
                'category': f'indexes_{key}',
                'source': f'major-indexes/{filename}',
                'last_updated': index_data['metadata']['generated_at']
            })
            print(f"   ✓ {key} indices loaded")
    
    if indexes_data:
        combined['data']['major_indexes'] = indexes_data
        set_block_status(
            combined,
            'major_indexes',
            status='ok' if any(not is_empty_value(v) for v in indexes_data.values()) else 'empty',
            reason=None,
            source='major-indexes/*.json',
            record_count=len(indexes_data),
        )
    else:
        set_block_status(
            combined,
            'major_indexes',
            status='missing',
            reason='No major-indexes snapshot files loaded',
            source='major-indexes/*.json',
        )
    
    # ==================== MEAN REVERSION ====================
    print("\n🎯 Loading mean reversion snapshots...")
    mean_reversion_data = {}
    
    ma_spreads = load_json_file(data_dir / 'meanreversion' / 'ma_spreads_snapshot.json')
    if ma_spreads:
        mean_reversion_data['ma_spreads'] = ma_spreads.get('data', {})
        combined['metadata']['data_sources'].append({
            'category': 'mean_reversion_ma_spreads',
            'source': 'meanreversion/ma_spreads_snapshot.json',
            'last_updated': ma_spreads['metadata']['generated_at']
        })
        print("   ✓ MA spreads loaded")
    
    price_vs_ma = load_json_file(data_dir / 'meanreversion' / 'price_vs_ma_snapshot.json')
    if price_vs_ma:
        mean_reversion_data['price_vs_ma'] = price_vs_ma.get('data', {})
        combined['metadata']['data_sources'].append({
            'category': 'mean_reversion_price_vs_ma',
            'source': 'meanreversion/price_vs_ma_snapshot.json',
            'last_updated': price_vs_ma['metadata']['generated_at']
        })
        print("   ✓ Price vs MA loaded")
    
    if mean_reversion_data:
        combined['data']['mean_reversion'] = mean_reversion_data
        set_block_status(
            combined,
            'mean_reversion',
            status='ok' if not is_empty_value(mean_reversion_data) else 'empty',
            source='meanreversion/*_snapshot.json',
            record_count=len(mean_reversion_data),
        )
    else:
        set_block_status(
            combined,
            'mean_reversion',
            status='missing',
            reason='No mean reversion snapshots loaded',
            source='meanreversion/*_snapshot.json',
        )

    # ==================== SUPPORT / RESISTENCE (PIVOTS + SMAS) ====================
    print("\n📐 Loading support/resistence levels...")
    support_resistence = load_json_file(data_dir / 'supportresistence' / 'support_resistence.json')
    if support_resistence:
        combined['data']['support_resistence'] = support_resistence.get('data', {})
        combined['metadata']['data_sources'].append({
            'category': 'support_resistence',
            'source': 'supportresistence/support_resistence.json',
            'last_updated': support_resistence.get('metadata', {}).get('generated_at', 'N/A')
        })
        set_block_status(
            combined,
            'support_resistence',
            status='ok' if not is_empty_value(combined['data'].get('support_resistence')) else 'empty',
            source='supportresistence/support_resistence.json',
            last_updated=support_resistence.get('metadata', {}).get('generated_at'),
        )
        print("   ✓ Support/resistence loaded")
    else:
        set_block_status(
            combined,
            'support_resistence',
            status='missing',
            reason='File missing or failed to load',
            source='supportresistence/support_resistence.json',
        )
    
    # ==================== IMPLIED VOLATILITY ====================
    print("\n📉 Loading implied volatility snapshots...")
    iv_data = {}
    
    vix_options = load_json_file(data_dir / 'implied-volatility' / 'vix_options_snapshot.json')
    if vix_options:
        iv_data['vix_options'] = vix_options.get('data', {})
        combined['metadata']['data_sources'].append({
            'category': 'implied_volatility_vix',
            'source': 'implied-volatility/vix_options_snapshot.json',
            'last_updated': vix_options.get('metadata', {}).get('generated_at', 'N/A')
        })
        print("   ✓ VIX options loaded")
    
    major_indices_iv = load_json_file(data_dir / 'implied-volatility' / 'major_indices_iv_snapshot.json')
    if major_indices_iv:
        iv_data['major_indices'] = major_indices_iv.get('data', {})
        combined['metadata']['data_sources'].append({
            'category': 'implied_volatility_indices',
            'source': 'implied-volatility/major_indices_iv_snapshot.json',
            'last_updated': major_indices_iv.get('metadata', {}).get('generated_at', 'N/A')
        })
        print("   ✓ Major indices IV loaded")
    
    sector_etfs_iv = load_json_file(data_dir / 'implied-volatility' / 'sector_etfs_iv_snapshot.json')
    if sector_etfs_iv:
        iv_data['sector_etfs'] = sector_etfs_iv.get('data', {})
        combined['metadata']['data_sources'].append({
            'category': 'implied_volatility_sectors',
            'source': 'implied-volatility/sector_etfs_iv_snapshot.json',
            'last_updated': sector_etfs_iv.get('metadata', {}).get('generated_at', 'N/A')
        })
        print("   ✓ Sector ETFs IV loaded")
    
    if iv_data:
        combined['data']['implied_volatility'] = iv_data
        set_block_status(
            combined,
            'implied_volatility',
            status='ok' if not is_empty_value(iv_data) else 'empty',
            source='implied-volatility/*_snapshot.json',
            record_count=len(iv_data),
        )
    else:
        set_block_status(
            combined,
            'implied_volatility',
            status='missing',
            reason='No implied volatility snapshots loaded',
            source='implied-volatility/*_snapshot.json',
        )
    
    # ==================== DAILY NEWS ====================
    print("\n📰 Loading daily news...")
    news_data = {}
    
    top_news = load_json_file(data_dir / 'daily-news' / 'top_news.json')
    if top_news:
        raw_top_news = top_news.get('data', [])
        if is_empty_value(raw_top_news):
            raw_top_news = top_news.get('articles', [])

        news_data['top_news'] = raw_top_news
        combined['metadata']['data_sources'].append({
            'category': 'news_top',
            'source': 'daily-news/top_news.json',
            'last_updated': top_news['metadata']['generated_at']
        })
        set_block_status(
            combined,
            'news_top',
            status='ok' if not is_empty_value(raw_top_news) else 'empty',
            source='daily-news/top_news.json',
            last_updated=top_news.get('metadata', {}).get('generated_at'),
            record_count=len(raw_top_news) if isinstance(raw_top_news, list) else None,
        )
        print("   ✓ Top news loaded")
    else:
        set_block_status(
            combined,
            'news_top',
            status='missing',
            reason='File missing or failed to load',
            source='daily-news/top_news.json',
        )
    
    sector_news = load_json_file(data_dir / 'daily-news' / 'sector_news.json')
    if sector_news:
        raw_sector_news = sector_news.get('data', {})
        if is_empty_value(raw_sector_news):
            raw_sector_news = sector_news.get('sectors', {})

        news_data['sector_news'] = raw_sector_news
        combined['metadata']['data_sources'].append({
            'category': 'news_sectors',
            'source': 'daily-news/sector_news.json',
            'last_updated': sector_news['metadata']['generated_at']
        })
        set_block_status(
            combined,
            'news_sectors',
            status='ok' if not is_empty_value(raw_sector_news) else 'empty',
            source='daily-news/sector_news.json',
            last_updated=sector_news.get('metadata', {}).get('generated_at'),
            record_count=len(raw_sector_news) if isinstance(raw_sector_news, dict) else None,
        )
        print("   ✓ Sector news loaded")
    else:
        set_block_status(
            combined,
            'news_sectors',
            status='missing',
            reason='File missing or failed to load',
            source='daily-news/sector_news.json',
        )

    # Add a writer-friendly normalized view (additive; keep raw blocks above)
    if top_news or sector_news:
        normalized: Dict[str, Any] = {}

        def normalize_article(article: Dict[str, Any]) -> Dict[str, Any]:
            return {
                'title': article.get('title') or article.get('headline'),
                'summary': article.get('summary'),
                'source': article.get('source'),
                'url': article.get('url'),
                'published_at': article.get('published_at') or article.get('datetime'),
                'timestamp': article.get('timestamp'),
                'category': article.get('category'),
                'id': article.get('id'),
                'ticker': article.get('ticker'),
            }

        raw_top = news_data.get('top_news') or []
        if isinstance(raw_top, list):
            normalized['top_news'] = [normalize_article(a) for a in raw_top if isinstance(a, dict)]

        raw_sectors = news_data.get('sector_news') or {}
        if isinstance(raw_sectors, dict):
            normalized_sectors: Dict[str, Any] = {}
            for sector_etf, sector_payload in raw_sectors.items():
                if not isinstance(sector_payload, dict):
                    continue
                articles = sector_payload.get('articles', [])
                normalized_sectors[sector_etf] = {
                    'sector_name': sector_payload.get('sector_name'),
                    'articles': [
                        {
                            **normalize_article(a),
                            'sector_etf': sector_etf,
                            'sector_name': sector_payload.get('sector_name'),
                        }
                        for a in articles
                        if isinstance(a, dict)
                    ],
                }
            normalized['sector_news'] = normalized_sectors

        if normalized:
            news_data['normalized'] = normalized
    
    if news_data:
        combined['data']['news'] = news_data
        set_block_status(
            combined,
            'news',
            status='ok' if not is_empty_value(news_data) else 'empty',
            source='daily-news/*.json',
        )
    else:
        set_block_status(
            combined,
            'news',
            status='missing',
            reason='No news blocks loaded',
            source='daily-news/*.json',
        )
    
    # ==================== ECONOMY INDICATORS ====================
    print("\n💰 Loading economy indicators...")
    economy_data = {}
    
    growth_output = load_json_file(data_dir / 'economy-breadth' / 'growth_output.json')
    if growth_output:
        economy_data['growth_output'] = growth_output.get('data', {})
        combined['metadata']['data_sources'].append({
            'category': 'economy_growth',
            'source': 'economy-breadth/growth_output.json',
            'last_updated': growth_output['metadata']['generated_at']
        })
        print("   ✓ Growth & output loaded")
    
    inflation_prices = load_json_file(data_dir / 'economy-breadth' / 'inflation_prices.json')
    if inflation_prices:
        economy_data['inflation_prices'] = inflation_prices.get('data', {})
        combined['metadata']['data_sources'].append({
            'category': 'economy_inflation',
            'source': 'economy-breadth/inflation_prices.json',
            'last_updated': inflation_prices['metadata']['generated_at']
        })
        print("   ✓ Inflation & prices loaded")
    
    labor_employment = load_json_file(data_dir / 'economy-breadth' / 'labor_employment.json')
    if labor_employment:
        economy_data['labor_employment'] = labor_employment.get('data', {})
        combined['metadata']['data_sources'].append({
            'category': 'economy_labor',
            'source': 'economy-breadth/labor_employment.json',
            'last_updated': labor_employment['metadata']['generated_at']
        })
        print("   ✓ Labor & employment loaded")
    
    money_markets = load_json_file(data_dir / 'economy-breadth' / 'money_markets.json')
    if money_markets:
        economy_data['money_markets'] = money_markets.get('data', {})
        combined['metadata']['data_sources'].append({
            'category': 'economy_money_markets',
            'source': 'economy-breadth/money_markets.json',
            'last_updated': money_markets['metadata']['generated_at']
        })
        print("   ✓ Money markets loaded")
    
    if economy_data:
        combined['data']['economy'] = economy_data
        set_block_status(
            combined,
            'economy',
            status='ok' if not is_empty_value(economy_data) else 'empty',
            source='economy-breadth/*.json',
            record_count=len(economy_data),
        )
    else:
        set_block_status(
            combined,
            'economy',
            status='missing',
            reason='No economy indicators loaded',
            source='economy-breadth/*.json',
        )

    # ==================== OPTIONAL MARKET PULSE CONTEXT ====================
    print("\n🧭 Loading optional Market Pulse context...")
    market_month = session_market_date[:7] if session_market_date else datetime.now(timezone.utc).strftime('%Y-%m')

    fund_flow_files = {
        'asset_class': f'etf_fund_flows_agg_asset_class_{market_month}.json',
        'category': f'etf_fund_flows_agg_category_{market_month}.json',
        'subcategory': f'etf_fund_flows_agg_subcategory_{market_month}.json',
    }
    fund_flows: Dict[str, Any] = {}
    fund_flow_last_updated: Optional[str] = None
    for key, filename in fund_flow_files.items():
        payload = load_json_file(data_dir / 'etf-fund-flows' / filename)
        if not payload:
            continue
        fund_flows[key] = payload
        last_updated = payload.get('metadata', {}).get('generated_at')
        if isinstance(last_updated, str):
            fund_flow_last_updated = last_updated
        combined['metadata']['data_sources'].append({
            'category': f'fund_flows_{key}',
            'source': f'etf-fund-flows/{filename}',
            'last_updated': last_updated or 'N/A',
        })
        print(f"   ✓ ETF fund flows loaded ({key})")

    if fund_flows:
        combined['data']['fund_flows'] = fund_flows
        fund_flow_status = 'ok'
        fund_flow_reason = None
        if is_stale_for_market_date(fund_flow_last_updated, session_market_date):
            fund_flow_status = 'stale'
            fund_flow_reason = 'Fund flow data is older than the market date'
        elif not has_meaningful_fund_flow_signal(fund_flows):
            fund_flow_status = 'low_relevance'
            fund_flow_reason = 'Fund flow files loaded but contain no measured flow values'
        set_block_status(
            combined,
            'fund_flows',
            status=fund_flow_status,
            reason=fund_flow_reason,
            source='etf-fund-flows/etf_fund_flows_agg_*_YYYY-MM.json',
            last_updated=fund_flow_last_updated,
            record_count=len(fund_flows),
        )
    else:
        set_block_status(
            combined,
            'fund_flows',
            status='missing',
            reason='No ETF fund flow aggregate files loaded for market month',
            source='etf-fund-flows/etf_fund_flows_agg_*_YYYY-MM.json',
        )

    options_whales = load_json_file(data_dir / 'options-whales' / 'options_whale_summary.json')
    if options_whales:
        combined['data']['options_whales'] = options_whales
        options_last_updated = options_whales.get('metadata', {}).get('generated_at')
        combined['metadata']['data_sources'].append({
            'category': 'options_whales',
            'source': 'options-whales/options_whale_summary.json',
            'last_updated': options_last_updated or 'N/A',
        })
        options_status = 'ok'
        options_reason = None
        if is_stale_for_market_date(options_last_updated, session_market_date):
            options_status = 'stale'
            options_reason = 'Options whale summary is older than the market date'
        elif get_whale_trade_count(options_whales) <= 0:
            options_status = 'low_relevance'
            options_reason = 'Options whale summary contains no whale trades'
        set_block_status(
            combined,
            'options_whales',
            status=options_status,
            reason=options_reason,
            source='options-whales/options_whale_summary.json',
            last_updated=options_last_updated,
            record_count=get_whale_trade_count(options_whales),
        )
        print("   ✓ Options whale summary loaded")
    else:
        set_block_status(
            combined,
            'options_whales',
            status='missing',
            reason='Options whale summary not loaded',
            source='options-whales/options_whale_summary.json',
        )

    stock_whales = load_json_file(data_dir / 'stock-whales' / 'stock_whale_summary.json')
    if stock_whales:
        combined['data']['stock_whales'] = stock_whales
        stock_last_updated = stock_whales.get('metadata', {}).get('generated_at') or stock_whales.get('metadata', {}).get('collection_timestamp')
        combined['metadata']['data_sources'].append({
            'category': 'stock_whales',
            'source': 'stock-whales/stock_whale_summary.json',
            'last_updated': stock_last_updated or 'N/A',
        })
        stock_status = 'ok'
        stock_reason = None
        if is_stale_for_market_date(stock_last_updated, session_market_date):
            stock_status = 'stale'
            stock_reason = 'Stock whale summary is older than the market date'
        elif get_whale_trade_count(stock_whales) <= 0:
            stock_status = 'low_relevance'
            stock_reason = 'Stock whale summary contains no whale trades'
        set_block_status(
            combined,
            'stock_whales',
            status=stock_status,
            reason=stock_reason,
            source='stock-whales/stock_whale_summary.json',
            last_updated=stock_last_updated,
            record_count=get_whale_trade_count(stock_whales),
        )
        print("   ✓ Stock whale summary loaded")
    else:
        set_block_status(
            combined,
            'stock_whales',
            status='missing',
            reason='Stock whale summary not loaded',
            source='stock-whales/stock_whale_summary.json',
        )
    
    # ==================== WEEKLY DATA (if available) ====================
    print("\n📅 Loading weekly data (if available)...")
    weekly_data = {}
    
    earnings_calendar = load_json_file(data_dir / 'earnings-calendar' / 'earnings_calendar.json')
    if earnings_calendar:
        weekly_data['earnings_calendar'] = earnings_calendar.get('data', {})
        combined['metadata']['data_sources'].append({
            'category': 'weekly_earnings_calendar',
            'source': 'earnings-calendar/earnings_calendar.json',
            'last_updated': earnings_calendar['metadata']['generated_at']
        })
        print("   ✓ Earnings calendar loaded")
    
    earnings_surprises = load_json_file(data_dir / 'earnings-surprises' / 'earnings_surprises.json')
    if earnings_surprises:
        weekly_data['earnings_surprises'] = earnings_surprises.get('data', {})
        combined['metadata']['data_sources'].append({
            'category': 'weekly_earnings_surprises',
            'source': 'earnings-surprises/earnings_surprises.json',
            'last_updated': earnings_surprises['metadata']['generated_at']
        })
        print("   ✓ Earnings surprises loaded")
    
    if weekly_data:
        combined['data']['weekly'] = weekly_data
        set_block_status(
            combined,
            'weekly',
            status='ok' if not is_empty_value(weekly_data) else 'empty',
            source='earnings-calendar/*.json, earnings-surprises/*.json',
            record_count=len(weekly_data),
        )
    else:
        set_block_status(
            combined,
            'weekly',
            status='missing',
            reason='No weekly datasets loaded',
            source='earnings-calendar/*.json, earnings-surprises/*.json',
        )

    # Finalize session date fields (writer-friendly + backward compatible)
    # Prefer the date sourced from a daily dataset.
    if session_market_date:
        combined['metadata']['market_date'] = session_market_date
        combined['metadata']['date'] = session_market_date

        previous_market_date = derive_previous_market_date(data_dir, session_market_date)
        if previous_market_date:
            combined['metadata']['previous_market_date'] = previous_market_date

    # ==================== WRITER-READY (Derived; Additive) ====================
    # These blocks are derived from raw blocks above, designed to support
    # repeatable Market Pulse tables without forcing downstream consumers to
    # interpret many source-specific shapes.
    writer_ready: Dict[str, Any] = {}

    major_indexes = combined.get('data', {}).get('major_indexes', {})
    us_major = major_indexes.get('us_major') if isinstance(major_indexes, dict) else None
    us_sectors = major_indexes.get('us_sectors') if isinstance(major_indexes, dict) else None
    implied_vol = combined.get('data', {}).get('implied_volatility', {})
    iv_major = implied_vol.get('major_indices') if isinstance(implied_vol, dict) else None
    iv_vix = implied_vol.get('vix_options') if isinstance(implied_vol, dict) else None
    support_res = combined.get('data', {}).get('support_resistence', {})

    # Pre-load US major historical series (used for lookback tables)
    us_major_history = load_json_file(data_dir / 'major-indexes' / 'us_major_indices_historical.json') or {}
    last_3_dates: list[str] = []
    last_5_dates: list[str] = []
    if session_market_date:
        last_3_dates = get_last_trading_dates_from_us_major_history(data_dir, session_market_date, count=3)
        last_5_dates = get_last_trading_dates_from_us_major_history(data_dir, session_market_date, count=5)

    # 0) Breadth table
    breadth = combined.get('data', {}).get('market_breadth')
    if isinstance(breadth, dict) and not is_empty_value(breadth):
        ad = breadth.get('advances_declines', {}) if isinstance(breadth.get('advances_declines'), dict) else {}
        volm = breadth.get('volume_metrics', {}) if isinstance(breadth.get('volume_metrics'), dict) else {}
        hl = breadth.get('new_highs_lows', {}) if isinstance(breadth.get('new_highs_lows'), dict) else {}
        ma = breadth.get('moving_averages', {}) if isinstance(breadth.get('moving_averages'), dict) else {}

        writer_ready['breadth_table'] = {
            'market_date': breadth.get('date') or combined.get('metadata', {}).get('market_date'),
            'advances': ad.get('advances'),
            'declines': ad.get('declines'),
            'unchanged': ad.get('unchanged'),
            'advance_decline_ratio': ad.get('advance_decline_ratio'),
            'advancing_volume_pct': volm.get('advancing_volume_pct'),
            'stocks_near_52w_high': hl.get('stocks_near_52w_high'),
            'stocks_near_52w_low': hl.get('stocks_near_52w_low'),
            'high_low_ratio': hl.get('high_low_ratio'),
            'above_20_day_ma_pct': (ma.get('above_20_day_ma') or {}).get('percentage') if isinstance(ma.get('above_20_day_ma'), dict) else None,
            'above_50_day_ma_pct': (ma.get('above_50_day_ma') or {}).get('percentage') if isinstance(ma.get('above_50_day_ma'), dict) else None,
            'above_200_day_ma_pct': (ma.get('above_200_day_ma') or {}).get('percentage') if isinstance(ma.get('above_200_day_ma'), dict) else None,
        }

    # 1) Major index performance table
    if isinstance(us_major, dict) and not is_empty_value(us_major):
        major_symbols = ['^GSPC', '^DJI', '^IXIC', '^RUT']
        rows = []
        for symbol in major_symbols:
            item = us_major.get(symbol)
            if not isinstance(item, dict):
                continue
            rows.append({
                'symbol': symbol,
                'name': item.get('name'),
                'close': item.get('current_price'),
                'change': item.get('daily_change'),
                'change_percent': item.get('daily_change_percent'),
            })
        if rows:
            writer_ready['major_indexes_table'] = rows

    # 2) Sector leaders / laggards (by 1-day %)
    if isinstance(us_sectors, dict) and not is_empty_value(us_sectors):
        sector_rows = []
        for symbol, item in us_sectors.items():
            if not isinstance(item, dict):
                continue
            sector_rows.append({
                'symbol': symbol,
                'sector_name': item.get('sector_name'),
                'close': item.get('current_price'),
                'change_percent': item.get('daily_change_percent'),
            })
        sector_rows = [r for r in sector_rows if isinstance(r.get('change_percent'), (int, float))]
        sector_rows.sort(key=lambda r: r['change_percent'], reverse=True)
        if sector_rows:
            writer_ready['sector_leaders'] = sector_rows[:5]
            writer_ready['sector_laggards'] = list(reversed(sector_rows[-5:]))

    # 3) Volatility summary
    vol: Dict[str, Any] = {}
    if isinstance(iv_vix, dict):
        # vix_options snapshot shapes may vary; attempt common keys
        vix_item = iv_vix.get('^VIX') if isinstance(iv_vix.get('^VIX'), dict) else None
        if not vix_item:
            vix_item = iv_vix.get('VIX') if isinstance(iv_vix.get('VIX'), dict) else None
        if vix_item:
            vol['vix'] = {
                'symbol': vix_item.get('symbol') or '^VIX',
                'close': vix_item.get('current_price') or vix_item.get('close') or vix_item.get('last'),
                'change': vix_item.get('daily_change'),
                'change_percent': vix_item.get('daily_change_percent'),
            }
    if isinstance(iv_major, dict) and not is_empty_value(iv_major):
        iv_rows = []
        for symbol in ['SPY', 'QQQ', 'IWM', 'DIA']:
            item = iv_major.get(symbol)
            if not isinstance(item, dict):
                continue
            iv_rows.append({
                'symbol': symbol,
                'average_iv': item.get('average_iv'),
                'average_iv_formatted': item.get('average_iv_formatted'),
                'iv_level': item.get('iv_level'),
            })
        if iv_rows:
            vol['major_index_iv'] = iv_rows
    if vol:
        writer_ready['volatility_summary'] = vol

    # 4) Technical levels (SPY by default)
    if isinstance(support_res, dict) and isinstance(support_res.get('SPY'), dict):
        spy_levels = support_res.get('SPY', {})
        writer_ready['technical_levels'] = {
            'SPY': {
                'reference_date': spy_levels.get('reference_bar', {}).get('date'),
                'traditional_pivots': spy_levels.get('traditional_pivots'),
                'fibonacci_pivots': spy_levels.get('fibonacci_pivots'),
                'sma': spy_levels.get('sma'),
            }
        }

    # 5) 3-day major index table (close + daily return %)
    if last_3_dates and isinstance(us_major_history, dict) and not is_empty_value(us_major_history):
        table_rows = []
        for symbol in ['^GSPC', '^DJI', '^IXIC', '^RUT']:
            lookup = build_close_return_lookup(us_major_history, symbol)
            if not lookup:
                continue
            # Prefer name from live snapshot when available
            name = None
            if isinstance(us_major, dict) and isinstance(us_major.get(symbol), dict):
                name = us_major.get(symbol, {}).get('name')
            if not name:
                indices = us_major_history.get('indices') if isinstance(us_major_history.get('indices'), dict) else None
                if isinstance(indices, dict) and isinstance(indices.get(symbol), dict):
                    name = indices.get(symbol, {}).get('name')

            values = []
            for d in last_3_dates:
                v = lookup.get(d)
                values.append({
                    'date': d,
                    'close': (v or {}).get('close'),
                    'daily_return_percent': (v or {}).get('daily_return_percent'),
                })
            table_rows.append({'symbol': symbol, 'name': name, 'values': values})

        if table_rows:
            writer_ready['index_table_3day'] = {
                'dates': last_3_dates,
                'rows': table_rows,
                'source': 'major-indexes/us_major_indices_historical.json',
            }

    # 5b) 5-day major index table (close + daily return %)
    if last_5_dates and isinstance(us_major_history, dict) and not is_empty_value(us_major_history):
        table_rows = []
        for symbol in ['^GSPC', '^DJI', '^IXIC', '^RUT']:
            lookup = build_close_return_lookup(us_major_history, symbol)
            if not lookup:
                continue

            name = None
            if isinstance(us_major, dict) and isinstance(us_major.get(symbol), dict):
                name = us_major.get(symbol, {}).get('name')
            if not name:
                indices = us_major_history.get('indices') if isinstance(us_major_history.get('indices'), dict) else None
                if isinstance(indices, dict) and isinstance(indices.get(symbol), dict):
                    name = indices.get(symbol, {}).get('name')

            values = []
            for d in last_5_dates:
                v = lookup.get(d)
                values.append({
                    'date': d,
                    'close': (v or {}).get('close'),
                    'daily_return_percent': (v or {}).get('daily_return_percent'),
                })
            table_rows.append({'symbol': symbol, 'name': name, 'values': values})

        if table_rows:
            writer_ready['index_table_5day'] = {
                'dates': last_5_dates,
                'rows': table_rows,
                'source': 'major-indexes/us_major_indices_historical.json',
            }

    # 6) 3-day VIX table (close + daily return %)
    if last_3_dates and isinstance(us_major_history, dict) and not is_empty_value(us_major_history):
        vix_lookup = build_close_return_lookup(us_major_history, '^VIX')
        if vix_lookup:
            vix_values = []
            for d in last_3_dates:
                v = vix_lookup.get(d)
                vix_values.append({
                    'date': d,
                    'close': (v or {}).get('close'),
                    'daily_return_percent': (v or {}).get('daily_return_percent'),
                })
            writer_ready['vix_table'] = {
                'dates': last_3_dates,
                'symbol': '^VIX',
                'name': 'CBOE Volatility Index',
                'values': vix_values,
                'source': 'major-indexes/us_major_indices_historical.json',
            }

    # 6b) 5-day VIX table (close + daily return %)
    if last_5_dates and isinstance(us_major_history, dict) and not is_empty_value(us_major_history):
        vix_lookup = build_close_return_lookup(us_major_history, '^VIX')
        if vix_lookup:
            vix_values = []
            for d in last_5_dates:
                v = vix_lookup.get(d)
                vix_values.append({
                    'date': d,
                    'close': (v or {}).get('close'),
                    'daily_return_percent': (v or {}).get('daily_return_percent'),
                })
            writer_ready['vix_table_5day'] = {
                'dates': last_5_dates,
                'symbol': '^VIX',
                'name': 'CBOE Volatility Index',
                'values': vix_values,
                'source': 'major-indexes/us_major_indices_historical.json',
            }

    # 7) 5-day SPY SMA table (20/50/200) from support/resistence history
    if last_5_dates and isinstance(support_res, dict):
        spy = support_res.get('SPY')
        if isinstance(spy, dict):
            history = ((spy.get('history') or {}).get('daily')) if isinstance(spy.get('history'), dict) else None
            if isinstance(history, list) and history:
                sma_lookup: Dict[str, Dict[str, Any]] = {}
                for row in history:
                    if not isinstance(row, dict):
                        continue
                    d = row.get('date')
                    sma = row.get('sma')
                    if isinstance(d, str) and isinstance(sma, dict):
                        sma_lookup[d] = sma

                values = []
                for d in last_5_dates:
                    sma = sma_lookup.get(d) or {}
                    values.append({
                        'date': d,
                        'SMA20': sma.get('SMA20'),
                        'SMA50': sma.get('SMA50'),
                        'SMA200': sma.get('SMA200'),
                    })

                writer_ready['spy_sma_table_5day'] = {
                    'dates': last_5_dates,
                    'symbol': 'SPY',
                    'name': 'SPDR S&P 500 ETF Trust',
                    'values': values,
                    'source': 'supportresistence/support_resistence.json',
                }

    # 8) 5-day breadth lookback (best-effort from historical series)
    if last_5_dates:
        ad_hist = load_json_file(data_dir / 'advance-decline' / 'ad_line_historical.json')
        ma_hist = load_json_file(data_dir / 'advance-decline' / 'ma_percentage_historical.json')
        hl_hist = load_json_file(data_dir / 'advance-decline' / 'highs_lows_historical.json')
        vol_hist = load_json_file(data_dir / 'advance-decline' / 'volume_metrics_historical.json')

        ad_lookup = build_simple_date_lookup(ad_hist)
        ma_lookup = build_simple_date_lookup(ma_hist)
        hl_lookup = build_simple_date_lookup(hl_hist)
        vol_lookup = build_simple_date_lookup(vol_hist)

        values = []
        for d in last_5_dates:
            ad_row = ad_lookup.get(d) or {}
            ma_row = ma_lookup.get(d) or {}
            hl_row = hl_lookup.get(d) or {}
            vol_row = vol_lookup.get(d) or {}

            advances = ad_row.get('advances')
            declines = ad_row.get('declines')
            ad_ratio = None
            if isinstance(advances, (int, float)) and isinstance(declines, (int, float)) and declines:
                ad_ratio = round(float(advances) / float(declines), 3)

            values.append({
                'date': d,
                'advances': advances,
                'declines': declines,
                'advance_decline_ratio': ad_ratio,
                'advancing_volume_pct': vol_row.get('advancing_volume_pct'),
                'stocks_near_52w_high': ((hl_row.get('near_52w_high') or {}).get('count')) if isinstance(hl_row.get('near_52w_high'), dict) else None,
                'stocks_near_52w_low': ((hl_row.get('near_52w_low') or {}).get('count')) if isinstance(hl_row.get('near_52w_low'), dict) else None,
                'above_20_day_ma_pct': ((ma_row.get('ma_20') or {}).get('percentage_above')) if isinstance(ma_row.get('ma_20'), dict) else None,
                'above_50_day_ma_pct': ((ma_row.get('ma_50') or {}).get('percentage_above')) if isinstance(ma_row.get('ma_50'), dict) else None,
                'above_200_day_ma_pct': ((ma_row.get('ma_200') or {}).get('percentage_above')) if isinstance(ma_row.get('ma_200'), dict) else None,
            })

        if values:
            writer_ready['breadth_lookback_5day'] = {
                'dates': last_5_dates,
                'values': values,
                'sources': {
                    'advances_declines': 'advance-decline/ad_line_historical.json',
                    'moving_averages': 'advance-decline/ma_percentage_historical.json',
                    'highs_lows': 'advance-decline/highs_lows_historical.json',
                    'volume': 'advance-decline/volume_metrics_historical.json',
                },
            }

    if writer_ready:
        combined['data']['writer_ready'] = writer_ready
        set_block_status(
            combined,
            'writer_ready',
            status='ok',
            reason='Derived from raw blocks in this snapshot',
            source='dailycombined/combine_daily_snapshots.py',
        )
    else:
        set_block_status(
            combined,
            'writer_ready',
            status='empty',
            reason='Insufficient inputs to derive writer-ready tables',
            source='dailycombined/combine_daily_snapshots.py',
        )
    
    # Add summary statistics
    combined['metadata']['total_sources'] = len(combined['metadata']['data_sources'])
    combined['metadata']['categories_included'] = list(combined['data'].keys())
    
    return combined


def main():
    """Main execution function."""
    print("=" * 80)
    print("COMBINING DAILY MARKET SNAPSHOTS")
    print("=" * 80)
    
    # Determine data directory (parent of this script's directory)
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent
    
    print(f"\n📂 Data directory: {data_dir}")
    print(f"📂 Output directory: {script_dir}")
    
    # Combine all snapshots
    combined_data = combine_snapshots(data_dir)
    
    # Save output files
    output_files = write_combined_outputs(combined_data, script_dir)
    output_file = output_files['market_snapshot']
    market_pulse_file = output_files['market_pulse_input']
    
    print("\n" + "=" * 80)
    print("✅ COMBINATION COMPLETE!")
    print("=" * 80)
    print(f"\n📁 Output: {output_file}")
    print(f"📁 Market Pulse input: {market_pulse_file}")
    print(f"📊 Total sources: {combined_data['metadata']['total_sources']}")
    print(f"📂 Categories: {', '.join(combined_data['metadata']['categories_included'])}")
    print(f"🕐 Generated: {combined_data['metadata']['generated_at']}")
    print(f"💾 File size: {output_file.stat().st_size / 1024:.1f} KB")
    print()


if __name__ == "__main__":
    main()
