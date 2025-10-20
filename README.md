# Binance Stock Price Streaming Pipeline

A real-time streaming data pipeline for Binance cryptocurrency prices using Apache Kafka, Flink, Spark, PostgreSQL, and Apache Superset.

## Architecture

```
Binance API → Kafka → Flink (Real-time Processing) → PostgreSQL
                ↓
              Spark (Batch Aggregation) → PostgreSQL → Superset Dashboard
```

## Components

### 1. **Kafka** (KRaft mode - no Zookeeper)
- Latest version with KRaft consensus
- Handles real-time message streaming
- Topic: `binance-prices`

### 2. **Binance Producer**
- Connects to Binance WebSocket API
- Streams real-time cryptocurrency prices
- Default symbols: BTC, ETH, BNB, ADA, SOL

### 3. **Flink Stream Processor**
- Consumes from Kafka in real-time
- Writes raw price data to PostgreSQL
- Low-latency processing

### 4. **Spark Batch Processor**
- Aggregates data every minute
- Creates 1-minute and 5-minute OHLC (Open, High, Low, Close) candles
- Updates materialized views

### 5. **PostgreSQL Database**
- Stores real-time and aggregated data
- Persistent storage with Docker volumes
- Tables:
  - `stock.real_time_prices` - Raw tick data
  - `stock.aggregated_prices_1min` - 1-minute candles
  - `stock.aggregated_prices_5min` - 5-minute candles
  - `stock.latest_prices` - Materialized view

### 6. **Apache Superset**
- Data visualization and dashboards
- Pre-configured PostgreSQL connection
- Default credentials: admin/admin123

## Prerequisites

- Docker
- Docker Compose
- 8GB+ RAM recommended
- Ports available: 5432, 8080, 8081, 8088, 9092

## Quick Start

### 1. Start all services:

```bash
docker-compose up -d
```

### 2. Check service status:

```bash
docker-compose ps
```

### 3. View logs:

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f binance-producer
docker-compose logs -f flink-processor
docker-compose logs -f spark-processor
```

### 4. Access UIs:

- **Superset Dashboard**: http://localhost:8088
  - Username: `admin`
  - Password: `admin123`
  
- **Flink Dashboard**: http://localhost:8081
  
- **Spark Dashboard**: http://localhost:8080

- **PostgreSQL**: 
  - Host: `localhost`
  - Port: `5432`
  - Database: `stock_data`
  - Username: `admin`
  - Password: `admin123`

## Configuration

### Change Trading Pairs

Edit `docker-compose.yml` and modify the `BINANCE_SYMBOLS` environment variable:

```yaml
binance-producer:
  environment:
    BINANCE_SYMBOLS: BTCUSDT,ETHUSDT,BNBUSDT,ADAUSDT,SOLUSDT,XRPUSDT
```

### Adjust Aggregation Intervals

Edit `spark-processor/spark_processor.py` to modify aggregation windows.

## Database Schema

### real_time_prices
```sql
- id (serial)
- symbol (varchar)
- price (decimal)
- timestamp (bigint)
- event_time (timestamp)
- volume (decimal)
- created_at (timestamp)
```

### aggregated_prices_1min / aggregated_prices_5min
```sql
- id (serial)
- symbol (varchar)
- window_start (timestamp)
- window_end (timestamp)
- open_price (decimal)
- close_price (decimal)
- high_price (decimal)
- low_price (decimal)
- avg_price (decimal)
- total_volume (decimal)
- trade_count (integer)
- created_at (timestamp)
```

## Creating Superset Dashboard

1. Access Superset at http://localhost:8088
2. Login with admin/admin123
3. Add Database Connection:
   - Go to **Settings** → **Database Connections**
   - Click **+ Database**
   - Select **PostgreSQL**
   - SQLAlchemy URI: `postgresql://admin:admin123@postgres:5432/stock_data`
   - Test connection and save

4. Create Dataset:
   - Go to **Data** → **Datasets**
   - Click **+ Dataset**
   - Select database, schema (`stock`), and table
   - Create datasets for:
     - `latest_prices` (current prices)
     - `aggregated_prices_1min` (1-min candles)
     - `aggregated_prices_5min` (5-min candles)

5. Create Charts:
   - **Time Series Line Chart**: Price over time
   - **Big Number**: Latest price by symbol
   - **Table**: Recent trades
   - **Area Chart**: Volume over time

6. Build Dashboard:
   - Go to **Dashboards** → **+ Dashboard**
   - Add charts to dashboard
   - Set auto-refresh (e.g., every 30 seconds)

## Data Persistence

All data is persisted in Docker volumes:
- `kafka-data` - Kafka logs and topics
- `postgres-data` - PostgreSQL database
- `flink-checkpoints` - Flink state
- `superset-data` - Superset configuration

**Data will NOT be lost on container restart.**

## Stopping Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes all data)
docker-compose down -v
```

## Troubleshooting

### Kafka not ready
Wait 20-30 seconds after starting for Kafka to fully initialize.

### No data in database
Check producer logs: `docker-compose logs binance-producer`

### Flink/Spark not processing
Ensure Kafka is running and topic exists:
```bash
docker exec -it kafka kafka-topics.sh --list --bootstrap-server localhost:9092
```

### Superset database connection fails
Make sure PostgreSQL is healthy:
```bash
docker-compose ps postgres
```

## Performance Tuning

### Increase Kafka partitions
Edit `docker-compose.yml`:
```yaml
kafka:
  environment:
    KAFKA_NUM_PARTITIONS: 6
```

### Scale Spark workers
```bash
docker-compose up -d --scale spark-worker=3
```

### Adjust batch intervals
Modify `spark_processor.py` sleep interval for more/less frequent aggregation.

## Monitoring

- **Kafka**: Check topic lag and consumer groups
- **Flink**: Monitor job status at http://localhost:8081
- **Spark**: Monitor jobs at http://localhost:8080
- **PostgreSQL**: Query table row counts
- **Superset**: View real-time dashboards

## Sample Queries

```sql
-- Latest prices
SELECT * FROM stock.latest_prices;

-- Last 100 trades for BTC
SELECT * FROM stock.real_time_prices 
WHERE symbol = 'BTCUSDT' 
ORDER BY event_time DESC 
LIMIT 100;

-- 1-minute candles for ETH (last hour)
SELECT * FROM stock.aggregated_prices_1min 
WHERE symbol = 'ETHUSDT' 
AND window_start >= NOW() - INTERVAL '1 hour'
ORDER BY window_start DESC;

-- Price statistics
SELECT 
    symbol,
    COUNT(*) as trade_count,
    MIN(price) as min_price,
    MAX(price) as max_price,
    AVG(price) as avg_price
FROM stock.real_time_prices
WHERE event_time >= NOW() - INTERVAL '1 hour'
GROUP BY symbol;
```

## License

MIT

## Contributing

Pull requests welcome!
