-- Sample queries for testing and monitoring the pipeline

-- 1. Check latest prices for all symbols
SELECT * FROM stock.latest_prices ORDER BY symbol;

-- 2. Count real-time records per symbol (last hour)
SELECT 
    symbol,
    COUNT(*) as record_count,
    MIN(event_time) as first_record,
    MAX(event_time) as last_record
FROM stock.real_time_prices
WHERE event_time >= NOW() - INTERVAL '1 hour'
GROUP BY symbol
ORDER BY symbol;

-- 3. Get latest 100 trades for Bitcoin
SELECT 
    symbol,
    price,
    volume,
    event_time
FROM stock.real_time_prices
WHERE symbol = 'BTCUSDT'
ORDER BY event_time DESC
LIMIT 100;

-- 4. View 1-minute aggregated candles (last hour)
SELECT 
    symbol,
    window_start,
    open_price,
    high_price,
    low_price,
    close_price,
    avg_price,
    total_volume,
    trade_count
FROM stock.aggregated_prices_1min
WHERE window_start >= NOW() - INTERVAL '1 hour'
ORDER BY symbol, window_start DESC;

-- 5. View 5-minute aggregated candles (last 6 hours)
SELECT 
    symbol,
    window_start,
    open_price,
    high_price,
    low_price,
    close_price,
    total_volume
FROM stock.aggregated_prices_5min
WHERE window_start >= NOW() - INTERVAL '6 hours'
ORDER BY symbol, window_start DESC;

-- 6. Calculate price change percentage (last 5 minutes)
WITH latest AS (
    SELECT DISTINCT ON (symbol)
        symbol,
        price as current_price,
        event_time
    FROM stock.real_time_prices
    ORDER BY symbol, event_time DESC
),
earlier AS (
    SELECT DISTINCT ON (symbol)
        symbol,
        price as earlier_price
    FROM stock.real_time_prices
    WHERE event_time <= NOW() - INTERVAL '5 minutes'
    ORDER BY symbol, event_time DESC
)
SELECT 
    l.symbol,
    l.current_price,
    e.earlier_price,
    ROUND(((l.current_price - e.earlier_price) / e.earlier_price * 100)::numeric, 2) as change_percent
FROM latest l
JOIN earlier e ON l.symbol = e.symbol
ORDER BY change_percent DESC;

-- 7. Get trading volume statistics (last hour)
SELECT 
    symbol,
    SUM(volume) as total_volume,
    AVG(volume) as avg_volume,
    MAX(volume) as max_volume,
    COUNT(*) as trade_count
FROM stock.real_time_prices
WHERE event_time >= NOW() - INTERVAL '1 hour'
GROUP BY symbol
ORDER BY total_volume DESC;

-- 8. Find price extremes (last 24 hours)
SELECT 
    symbol,
    MIN(price) as lowest_price,
    MAX(price) as highest_price,
    MAX(price) - MIN(price) as price_range,
    ROUND((((MAX(price) - MIN(price)) / MIN(price)) * 100)::numeric, 2) as range_percent
FROM stock.real_time_prices
WHERE event_time >= NOW() - INTERVAL '24 hours'
GROUP BY symbol
ORDER BY range_percent DESC;

-- 9. Refresh materialized view manually
REFRESH MATERIALIZED VIEW stock.latest_prices;

-- 10. Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'stock'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- 11. Monitor data freshness (check latest record per symbol)
SELECT 
    symbol,
    MAX(event_time) as latest_update,
    NOW() - MAX(event_time) as time_since_update
FROM stock.real_time_prices
GROUP BY symbol
ORDER BY latest_update DESC;

-- 12. Get moving average (simple 10-record MA)
WITH ranked_prices AS (
    SELECT 
        symbol,
        price,
        event_time,
        ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY event_time DESC) as rn
    FROM stock.real_time_prices
)
SELECT 
    symbol,
    AVG(price) as moving_avg_10
FROM ranked_prices
WHERE rn <= 10
GROUP BY symbol
ORDER BY symbol;
