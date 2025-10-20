-- Create schema for stock data
CREATE SCHEMA IF NOT EXISTS stock;

-- Raw real-time prices table (from Flink)
CREATE TABLE IF NOT EXISTS stock.real_time_prices (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    price DECIMAL(20, 8) NOT NULL,
    timestamp BIGINT NOT NULL,
    event_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    volume DECIMAL(20, 8),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_real_time_prices_symbol ON stock.real_time_prices(symbol);
CREATE INDEX idx_real_time_prices_timestamp ON stock.real_time_prices(timestamp);
CREATE INDEX idx_real_time_prices_event_time ON stock.real_time_prices(event_time);

-- Aggregated prices table (from Spark - 1 minute aggregates)
CREATE TABLE IF NOT EXISTS stock.aggregated_prices_1min (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,
    open_price DECIMAL(20, 8) NOT NULL,
    close_price DECIMAL(20, 8) NOT NULL,
    high_price DECIMAL(20, 8) NOT NULL,
    low_price DECIMAL(20, 8) NOT NULL,
    avg_price DECIMAL(20, 8) NOT NULL,
    total_volume DECIMAL(20, 8),
    trade_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, window_start)
);

CREATE INDEX idx_agg_1min_symbol ON stock.aggregated_prices_1min(symbol);
CREATE INDEX idx_agg_1min_window_start ON stock.aggregated_prices_1min(window_start);

-- Aggregated prices table (5 minute aggregates)
CREATE TABLE IF NOT EXISTS stock.aggregated_prices_5min (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,
    open_price DECIMAL(20, 8) NOT NULL,
    close_price DECIMAL(20, 8) NOT NULL,
    high_price DECIMAL(20, 8) NOT NULL,
    low_price DECIMAL(20, 8) NOT NULL,
    avg_price DECIMAL(20, 8) NOT NULL,
    total_volume DECIMAL(20, 8),
    trade_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, window_start)
);

CREATE INDEX idx_agg_5min_symbol ON stock.aggregated_prices_5min(symbol);
CREATE INDEX idx_agg_5min_window_start ON stock.aggregated_prices_5min(window_start);

-- Latest prices materialized view
CREATE MATERIALIZED VIEW IF NOT EXISTS stock.latest_prices AS
SELECT DISTINCT ON (symbol)
    symbol,
    price,
    timestamp,
    event_time,
    volume
FROM stock.real_time_prices
ORDER BY symbol, event_time DESC;

CREATE UNIQUE INDEX idx_latest_prices_symbol ON stock.latest_prices(symbol);

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA stock TO admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA stock TO admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA stock TO admin;
