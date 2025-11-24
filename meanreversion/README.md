# Mean Reversion Indicators

**Statistical analysis of price deviations from moving averages and MA spread patterns**

This dataset provides comprehensive mean reversion metrics for major US market indices, enabling traders and analysts to identify overbought/oversold conditions and potential mean reversion opportunities using institutional-grade statistical measures.

## 📊 Overview

Mean reversion is a financial theory suggesting that asset prices and historical returns eventually revert to their long-term mean or average level. This dataset tracks two primary mean reversion strategies used by professional traders:

1. **Price vs Moving Average**: How far current price has deviated from key moving averages
2. **Moving Average Spreads**: How wide the gap between MA pairs has become

## 📁 Data Files

### Price vs Moving Average
- **`price_vs_ma_snapshot.json`** - Current price deviation from 20/50/200-day MAs
- **`price_vs_ma_historical.json`** - 504-day historical price vs MA metrics

### Moving Average Spreads  
- **`ma_spreads_snapshot.json`** - Current spreads between MA pairs
- **`ma_spreads_historical.json`** - 504-day historical MA spread metrics

## 🎯 Indices Tracked

- **^GSPC** - S&P 500 (Large-cap benchmark)
- **^IXIC** - Nasdaq Composite (Tech-heavy)
- **^RUT** - Russell 2000 (Small-cap benchmark)

## 📈 Moving Averages

All calculations use Simple Moving Averages (SMA):
- **20-day MA** (Green #10b981) - Short-term trend (~1 month)
- **50-day MA** (Blue primary) - Intermediate trend (~2.5 months)
- **200-day MA** (Purple #9333ea) - Long-term trend (~1 year)

## 🧮 Metrics Explained

### Price vs MA Metrics

#### 1. Distance (Points)
```
Formula: current_price - ma_value
```
- **Positive** = Price above MA (bullish)
- **Negative** = Price below MA (bearish)
- **Large magnitude** = Extended from MA (potential reversion)

#### 2. Distance Percent
```
Formula: (current_price - ma_value) / ma_value × 100
```
- **>5%** = Significantly overbought
- **2% to 5%** = Moderately overbought
- **-2% to 2%** = Normal range
- **-5% to -2%** = Moderately oversold
- **<-5%** = Significantly oversold

#### 3. Z-Score (Statistical)
```
Formula: (current_price - ma) / std_dev(price - ma)
Lookback: 252 days (1 trading year)
```
- **>2** = Statistically overbought (>95th percentile) ⚠️ **Strong mean reversion signal**
- **1 to 2** = Moderately overbought
- **-1 to 1** = Normal statistical range
- **-2 to -1** = Moderately oversold
- **<-2** = Statistically oversold (<5th percentile) ⚠️ **Strong mean reversion signal**

**Why Z-Score Matters**: This is the institutional standard for mean reversion because it normalizes deviations across different market conditions and volatility regimes.

### MA Spread Metrics

#### 1. Spread (Points)
```
Formula: ma_short - ma_long
```
- **Positive** = Bullish alignment (short MA above long MA)
- **Negative** = Bearish alignment (short MA below long MA)
- **Large magnitude** = Wide spread suggests potential snapback

#### 2. Spread Percent
```
Formula: (ma_short - ma_long) / ma_long × 100
```
Normalizes spread for comparison across different price levels and instruments.

#### 3. Spread Z-Score
```
Formula: (current_spread - mean_spread) / std_dev(spread)
Lookback: 252 days
```
- **>2** = Extremely wide spread - **Mean reversion likely** (spread will narrow)
- **1 to 2** = Moderately wide spread
- **-1 to 1** = Normal spread range
- **-2 to -1** = Moderately narrow spread
- **<-2** = Extremely narrow spread - Potential breakout or trend reversal

**Professional Usage**: This is the most common institutional method for MA spread mean reversion.

## 🎯 MA Pairs Analyzed

### 20-day vs 50-day (short_term_vs_intermediate)
- **Timeframe**: Swing trading (days to weeks)
- **Use**: Short-term entries/exits
- **Crossover**: Quick trend change signals

### 20-day vs 200-day (short_term_vs_long_term)  
- **Timeframe**: Trend validation (weeks to months)
- **Use**: Confirm major trend direction
- **Extreme spreads**: Strong overbought/oversold signals

### 50-day vs 200-day (intermediate_vs_long_term)
- **Timeframe**: Major trend changes (months to years)
- **Use**: Golden Cross / Death Cross signals
- **Golden Cross**: 50-day crosses above 200-day (bullish)
- **Death Cross**: 50-day crosses below 200-day (bearish)

## 📊 Trading Applications

### Mean Reversion Strategy
Use extreme z-scores as contrarian signals:
- **Entry**: Z-score < -2 (look for longs) or > 2 (look for shorts)
- **Exit**: Z-score returns to 0 (mean reversion complete)
- **Confirmation**: Price crosses back through the MA

### Trend Following Filter
Combine with trend direction:
- Only take longs when price > 200-day MA
- Only take shorts when price < 200-day MA
- Strongest signals when all MAs aligned (20 > 50 > 200)

### MA Crossover Confirmation
Monitor MA spreads for trend changes:
- **Bullish**: 20-day crosses above 50-day
- **Bearish**: 20-day crosses below 50-day  
- **Golden Cross**: 50-day crosses above 200-day (major bullish)
- **Death Cross**: 50-day crosses below 200-day (major bearish)

### Extreme Spread Trading
When MA spread z-score is extreme:
- **Z > 2**: Spread too wide, expect narrowing (mean reversion)
- **Z < -2**: Spread too narrow, expect widening or reversal

## 💡 Professional Tips

1. **Z-Scores are King**: Professionals focus on z-scores over simple percentage deviations because they account for volatility changes
2. **Combine Multiple Timeframes**: Use 20-day for entries, 50-day for confirmation, 200-day for trend filter
3. **Watch for Alignment**: Strongest signals occur when all MAs point the same direction
4. **Mean Reversion Works Best in Ranges**: Be cautious during strong trends
5. **Statistical Significance**: Z-scores >2 or <-2 represent the top 5% of historical deviations

## 📅 Data Specifications

- **Update Frequency**: Every 15 minutes during market hours (9:30am - 4:15pm ET)
- **Historical Period**: 504 trading days (~2 years)
- **Z-Score Lookback**: 252 trading days (1 year)
- **Data Source**: Yahoo Finance (yfinance)
- **Calculation Method**: Simple Moving Averages (SMA)
- **Price Data**: Adjusted closing prices

## 🔧 Data Quality

All calculations require minimum data points:
- **20-day MA**: 20 days minimum
- **50-day MA**: 50 days minimum
- **200-day MA**: 200 days minimum
- **Z-Scores**: 252 days minimum

Insufficient data periods will show `null` values.

## 📖 Example Usage

### Identifying Overbought Conditions
```javascript
// Price vs MA approach
if (price_vs_ma.metrics_by_ma.ma_50.zscore > 2) {
  console.log("S&P 500 is statistically overbought vs 50-day MA");
  console.log("Mean reversion likely - consider profit taking or shorts");
}

// MA spread approach  
if (ma_spreads.ma_pairs.short_term_vs_intermediate.zscore > 2) {
  console.log("20/50-day MA spread extremely wide");
  console.log("Expect spread to narrow (potential pullback)");
}
```

### Detecting Golden Cross
```javascript
const spread_50_200 = ma_spreads.ma_pairs.intermediate_vs_long_term;

if (spread_50_200.spread > 0 && spread_50_200.alignment === 'bullish') {
  console.log("Golden Cross detected! 50-day above 200-day");
  console.log("Long-term bullish signal");
}
```

## 🎨 UI/UX Guidelines

When displaying this data in applications:
- **Color Coding**: 20-day = Green (#10b981), 50-day = Blue, 200-day = Purple (#9333ea)
- **Z-Score Badges**: 
  - Green (>2): Overbought
  - Orange (-2 to 2): Normal
  - Red (<-2): Oversold
- **Charts**: Include all three MAs with consistent colors
- **Alerts**: Highlight when z-scores exceed ±2

## 📚 References

- **Mean Reversion Theory**: Statistical tendency for prices to revert to historical average
- **Moving Averages**: Standard technical indicators for trend identification
- **Z-Scores**: Standard deviations from mean (statistical significance)
- **Golden/Death Cross**: Classic MA crossover signals used by institutional traders

## 🔗 Related Datasets

- **major-indexes/** - Base price data and technical indicators
- **advance-decline/** - Market breadth indicators
- **implied-volatility/** - Volatility metrics (VIX)

---

**Questions or Issues?** See the main [deanfi-data README](../README.md) or visit [DeanFinancials.com](https://deanfinancials.com)
