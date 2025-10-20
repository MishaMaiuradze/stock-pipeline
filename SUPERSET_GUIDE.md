# Superset Dashboard Setup Guide

This guide will help you create comprehensive dashboards in Apache Superset for monitoring Binance cryptocurrency prices.

## Step 1: Access Superset

1. Make sure all services are running: `./start.sh`
2. Wait about 30 seconds for Superset to fully initialize
3. Open browser and go to: http://localhost:8088
4. Login with:
   - Username: `admin`
   - Password: `admin123`

## Step 2: Add Database Connection

1. Click on **Settings** (top right) → **Database Connections**
2. Click **+ Database** button
3. Select **PostgreSQL** from supported databases
4. Fill in connection details:
   ```
   Display Name: Stock Data PostgreSQL
   SQLAlchemy URI: postgresql://admin:admin123@postgres:5432/stock_data
   ```
5. Click **Test Connection** - should show "Connection looks good!"
6. Click **Connect**

## Step 3: Add Datasets

### Dataset 1: Latest Prices (Real-time)

1. Go to **Data** → **Datasets**
2. Click **+ Dataset**
3. Select:
   - Database: `Stock Data PostgreSQL`
   - Schema: `stock`
   - Table: `latest_prices`
4. Click **Add** and then **Create Dataset and Create Chart**

### Dataset 2: Real-time Prices

1. Repeat above for table: `real_time_prices`

### Dataset 3: 1-Minute Aggregates

1. Repeat for table: `aggregated_prices_1min`

### Dataset 4: 5-Minute Aggregates

1. Repeat for table: `aggregated_prices_5min`

## Step 4: Create Charts

### Chart 1: Current Prices (Big Number with Trendline)

1. From `latest_prices` dataset
2. Chart Type: **Big Number with Trendline**
3. Query section:
   - **Metric**: `AVG(price)`
   - **Filters**: Add filter for specific symbol (e.g., `symbol = 'BTCUSDT'`)
4. Customize:
   - Chart Title: "Bitcoin (BTC) Current Price"
   - Number Format: `$,.2f`
5. Save chart: "BTC Current Price"
6. Repeat for other symbols (ETH, BNB, etc.)

### Chart 2: Price Time Series (Line Chart)

1. From `aggregated_prices_1min` dataset
2. Chart Type: **Time-series Line Chart**
3. Query section:
   - **Time Column**: `window_start`
   - **Metrics**: `AVG(avg_price)`
   - **Group by**: `symbol`
   - **Time Range**: Last 1 hour
4. Customize:
   - Chart Title: "Cryptocurrency Prices (1-Minute)"
   - Show Legend: Yes
   - Line Style: Smooth
5. Save chart: "Price Time Series"

### Chart 3: OHLC Candlestick Chart

1. From `aggregated_prices_5min` dataset
2. Chart Type: **Time-series Bar Chart** (or use custom viz if available)
3. Query section:
   - **Time Column**: `window_start`
   - **Metrics**:
     - `MAX(high_price)` (High)
     - `MIN(low_price)` (Low)
     - `AVG(open_price)` (Open)
     - `AVG(close_price)` (Close)
   - **Filters**: Select one symbol
   - **Time Range**: Last 6 hours
4. Save chart: "BTC Candlestick (5min)"

### Chart 4: Volume Chart

1. From `aggregated_prices_1min` dataset
2. Chart Type: **Time-series Bar Chart**
3. Query section:
   - **Time Column**: `window_start`
   - **Metric**: `SUM(total_volume)`
   - **Group by**: `symbol`
   - **Time Range**: Last 1 hour
4. Customize:
   - Chart Title: "Trading Volume"
   - Show Legend: Yes
5. Save chart: "Trading Volume"

### Chart 5: Price Comparison (Table)

1. From `latest_prices` dataset
2. Chart Type: **Table**
3. Query section:
   - **Columns**: `symbol`, `price`, `volume`, `event_time`
   - **Metrics**: None (using columns)
   - **Sort by**: `price` DESC
4. Customize:
   - Chart Title: "Current Prices Summary"
   - Page Size: 10
5. Save chart: "Price Summary Table"

### Chart 6: Price Distribution (Histogram)

1. From `real_time_prices` dataset
2. Chart Type: **Histogram**
3. Query section:
   - **Numeric Column**: `price`
   - **Filters**: Select one symbol, time range = last 1 hour
   - **Number of Bins**: 20
4. Save chart: "BTC Price Distribution"

### Chart 7: Trading Activity (Heatmap)

1. From `aggregated_prices_1min` dataset
2. Chart Type: **Heatmap**
3. Query section:
   - **Rows**: `symbol`
   - **Columns**: `window_start` (grouped by hour)
   - **Metric**: `SUM(trade_count)`
   - **Time Range**: Last 24 hours
4. Save chart: "Trading Activity Heatmap"

## Step 5: Create Dashboard

1. Go to **Dashboards** → Click **+ Dashboard**
2. Name it: "Binance Cryptocurrency Monitor"
3. Click **Save**

### Dashboard Layout:

#### Row 1: Current Prices (Big Numbers)
- Add all "Current Price" charts side by side
- BTC | ETH | BNB | ADA | SOL

#### Row 2: Main Price Chart
- Add "Price Time Series" chart (full width)

#### Row 3: Volume and Distribution
- Left: "Trading Volume" chart
- Right: "Price Summary Table"

#### Row 4: Detailed Analysis
- Left: "BTC Candlestick" chart
- Right: "Trading Activity Heatmap"

### Configure Auto-Refresh:

1. Edit Dashboard
2. Click **Settings** (gear icon)
3. Set **Auto-refresh interval**: 30 seconds or 1 minute
4. Save Dashboard

## Step 6: Create Filters

1. Edit Dashboard
2. Click **Filter** icon
3. Add filters:
   - **Symbol Filter**: Type = Select, Column = `symbol`
   - **Time Range Filter**: Type = Time range
4. Apply filters to relevant charts
5. Save Dashboard

## Sample Dashboard Queries

### Custom SQL Chart: Price Change %

1. Create new chart from SQL Lab
2. Go to **SQL** → **SQL Lab**
3. Select database: `Stock Data PostgreSQL`
4. Run query:

```sql
WITH latest AS (
    SELECT DISTINCT ON (symbol)
        symbol,
        price as current_price
    FROM stock.real_time_prices
    ORDER BY symbol, event_time DESC
),
hour_ago AS (
    SELECT DISTINCT ON (symbol)
        symbol,
        price as hour_ago_price
    FROM stock.real_time_prices
    WHERE event_time <= NOW() - INTERVAL '1 hour'
    ORDER BY symbol, event_time DESC
)
SELECT 
    l.symbol,
    l.current_price,
    h.hour_ago_price,
    ROUND(((l.current_price - h.hour_ago_price) / h.hour_ago_price * 100)::numeric, 2) as change_percent
FROM latest l
JOIN hour_ago h ON l.symbol = h.symbol
ORDER BY change_percent DESC;
```

5. Click **Save** → **Save as Dataset**
6. Create chart from this dataset

## Advanced Tips

### 1. Native Filters

Use native filters for better interactivity:
- Dashboard → Edit → Add filter
- Select column-based filters
- Enable "Apply to all applicable charts"

### 2. Cross-filtering

Enable cross-filtering between charts:
- Edit chart → Advanced → Enable emit filter
- Other charts will filter when you click on data points

### 3. Alerts

Set up alerts for price thresholds:
- Chart → Alerts & Reports
- Create new alert
- Set conditions (e.g., BTC price > $50,000)
- Configure notification method

### 4. Custom CSS

Customize dashboard appearance:
- Dashboard → Edit → Advanced → CSS
- Add custom styles for colors, fonts, etc.

### 5. Embedding

Embed dashboards in other applications:
- Dashboard → Share → Copy link
- Use iframe or API integration

## Monitoring Best Practices

1. **Set appropriate refresh rates**: 
   - Real-time data: 30 seconds
   - Aggregated data: 1-5 minutes

2. **Use filters effectively**:
   - Add symbol filters to allow users to focus on specific cryptocurrencies
   - Time range filters for historical analysis

3. **Optimize queries**:
   - Use aggregated tables for longer time ranges
   - Add indexes on frequently queried columns

4. **Create multiple dashboards**:
   - Overview dashboard (all symbols)
   - Symbol-specific dashboards (detailed analysis)
   - Performance dashboard (system metrics)

## Troubleshooting

### Cannot connect to database
- Verify PostgreSQL is running: `docker-compose ps postgres`
- Check connection string is correct
- Ensure network connectivity between Superset and PostgreSQL

### No data showing in charts
- Check if data is being ingested: Run queries in SQL Lab
- Verify filters are not too restrictive
- Check time range settings

### Charts not auto-refreshing
- Verify auto-refresh is enabled in dashboard settings
- Check browser console for errors
- Refresh page manually to test

## Sample Dashboard Export

After creating your dashboard, you can export it:
1. Dashboard → ... (menu) → Export
2. Save the ZIP file
3. Import on another Superset instance using **Import** function

Enjoy your real-time cryptocurrency monitoring dashboard! 🚀
