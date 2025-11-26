#!/usr/bin/env python3
"""
Combine Daily Market Snapshots

This script combines all daily snapshot data from various collectors into a single
comprehensive market snapshot JSON file for easy consumption by client applications.

Daily Snapshot Sources:
- advance-decline/daily_breadth.json - Market breadth indicators
- major-indexes/*.json (snapshot versions) - Major market indices
- meanreversion/*_snapshot.json - Mean reversion metrics
- implied-volatility/*_snapshot.json - Implied volatility data
- daily-news/*.json - Market news
- economy-breadth/*.json - Economic indicators

Output: market_snapshot.json - Combined snapshot with all daily data
"""
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional


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


def combine_snapshots(data_dir: Path) -> Dict[str, Any]:
    """
    Combine all daily snapshot data into a single structure.
    
    Args:
        data_dir: Path to the deanfi-data directory
        
    Returns:
        Dictionary with combined snapshot data
    """
    combined = {
        'metadata': {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'description': 'Combined daily market snapshot from all data collectors',
            'data_sources': [],
            'update_schedule': 'Updated after market close (approximately 4:38pm ET on weekdays)'
        },
        'data': {}
    }
    
    # ==================== MARKET BREADTH ====================
    print("\n📊 Loading market breadth data...")
    daily_breadth = load_json_file(data_dir / 'advance-decline' / 'daily_breadth.json')
    if daily_breadth:
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
        print("   ✓ Market breadth loaded")
    
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
            indexes_data[key] = index_data.get('data', {})
            combined['metadata']['data_sources'].append({
                'category': f'indexes_{key}',
                'source': f'major-indexes/{filename}',
                'last_updated': index_data['metadata']['generated_at']
            })
            print(f"   ✓ {key} indices loaded")
    
    if indexes_data:
        combined['data']['major_indexes'] = indexes_data
    
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
    
    # ==================== DAILY NEWS ====================
    print("\n📰 Loading daily news...")
    news_data = {}
    
    top_news = load_json_file(data_dir / 'daily-news' / 'top_news.json')
    if top_news:
        news_data['top_news'] = top_news.get('data', [])
        combined['metadata']['data_sources'].append({
            'category': 'news_top',
            'source': 'daily-news/top_news.json',
            'last_updated': top_news['metadata']['generated_at']
        })
        print("   ✓ Top news loaded")
    
    sector_news = load_json_file(data_dir / 'daily-news' / 'sector_news.json')
    if sector_news:
        news_data['sector_news'] = sector_news.get('data', {})
        combined['metadata']['data_sources'].append({
            'category': 'news_sectors',
            'source': 'daily-news/sector_news.json',
            'last_updated': sector_news['metadata']['generated_at']
        })
        print("   ✓ Sector news loaded")
    
    if news_data:
        combined['data']['news'] = news_data
    
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
    
    # Save to JSON file
    output_file = script_dir / 'market_snapshot.json'
    with open(output_file, 'w') as f:
        json.dump(combined_data, f, indent=2)
    
    print("\n" + "=" * 80)
    print("✅ COMBINATION COMPLETE!")
    print("=" * 80)
    print(f"\n📁 Output: {output_file}")
    print(f"📊 Total sources: {combined_data['metadata']['total_sources']}")
    print(f"📂 Categories: {', '.join(combined_data['metadata']['categories_included'])}")
    print(f"🕐 Generated: {combined_data['metadata']['generated_at']}")
    print(f"💾 File size: {output_file.stat().st_size / 1024:.1f} KB")
    print()


if __name__ == "__main__":
    main()
