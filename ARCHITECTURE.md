# System Architecture

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         BINANCE WEBSOCKET API                           │
│                    (Real-time Cryptocurrency Prices)                    │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 │ WebSocket Stream
                                 │
                    ┌────────────▼────────────┐
                    │  Binance Producer       │
                    │  (Python Container)     │
                    │  - WebSocket Client     │
                    │  - Data Serialization   │
                    └────────────┬────────────┘
                                 │
                                 │ JSON Messages
                                 │
                    ┌────────────▼────────────┐
                    │   Apache Kafka          │
                    │   (KRaft Mode)          │
                    │   Topic: binance-prices │
                    │   - No Zookeeper        │
                    │   - 3 Partitions        │
                    └────────┬────────────────┘
                             │
                             │ Stream
                             │
                    ┌────────▼─────────┐
                    │ Kafka Consumer   │
                    │ (Real-time)      │
                    │                  │
                    │ - Low latency    │
                    │ - Raw data write │
                    │ - Python consumer│
                    └────────┬─────────┘
                             │
                             │ INSERT real_time_prices
                             │
                ┌────────────▼────────────┐
                │   PostgreSQL 16         │
                │                         │
                │ Tables:                 │
                │ ├─ real_time_prices     │◄─────┐
                │ ├─ aggregated_1min      │      │
                │ ├─ aggregated_5min      │      │ JDBC Read
                │ └─ latest_prices (MV)   │      │
                │                         │      │
                │ Volumes:                │      │
                │ └─ postgres-data        │      │
                └────────────┬────────────┘      │
                             │                   │
                             │ INSERT Aggregates │
                             │                   │
                    ┌────────▼─────────┐         │
                    │  Spark Processor │─────────┘
                    │  (Batch)         │
                    │                  │ Reads from PostgreSQL
                    │ - Reads real_time│ every 60 seconds
                    │ - 1-min OHLC     │
                    │ - 5-min OHLC     │
                    │ - Writes back    │
                    └──────────────────┘

                ┌────────────▼────────────┐
                │  Apache Superset        │
                │                         │
                │ - Real-time dashboards  │
                │ - Custom charts         │
                │ - Alerts & reports      │
                │ - Auto-refresh          │
                └─────────────────────────┘
```

## Container Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Docker Network: stock-network                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │   Kafka      │  │  Postgres    │  │  Superset    │            │
│  │  Port: 9092  │  │  Port: 5432  │  │  Port: 8088  │            │
│  │              │  │              │  │              │            │
│  │  Volume:     │  │  Volume:     │  │  Volume:     │            │
│  │  kafka-data  │  │  postgres-   │  │  superset-   │            │
│  │              │  │  data        │  │  data        │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐                               │
│  │   Spark      │  │   Spark      │                               │
│  │   Master     │  │   Worker     │                               │
│  │  Port: 8080  │  │              │                               │
│  │  Port: 7077  │  │  2G RAM      │                               │
│  │              │  │  2 Cores     │                               │
│  │  Volume:     │  │              │                               │
│  │  spark-apps  │  │  Volume:     │                               │
│  │  spark-data  │  │  spark-apps  │                               │
│  └──────────────┘  └──────────────┘                               │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │  Binance     │  │   Kafka      │  │   Spark      │            │
│  │  Producer    │  │  Consumer    │  │  Processor   │            │
│  │              │  │              │  │              │            │
│  │  Python 3.11 │  │  Python 3.11 │  │  Python 3.9  │            │
│  │  WebSocket   │  │  Kafka       │  │  PySpark     │            │
│  │  Client      │  │  Consumer    │  │              │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Technology Stack

### Message Streaming
- **Apache Kafka 3.7.0** (KRaft mode)
  - No Zookeeper dependency
  - Self-managed metadata quorum
  - Persistent message queue
  - 3 partitions for load balancing

### Stream Processing
- **Python Kafka Consumer** (kafka-python library)
  - Real-time data processing
  - Direct Kafka consumption
  - Low-latency ingestion
  - Connection pooling to PostgreSQL
  - Consumer group coordination

### Batch Processing
- **Apache Spark 3.4.1**
  - Reads from PostgreSQL (real_time_prices table)
  - Window-based analytics (1-min and 5-min)
  - OHLC candle generation
  - Scheduled batch jobs (every 60 seconds)
  - Writes aggregations back to PostgreSQL

### Data Storage
- **PostgreSQL 16**
  - ACID compliance
  - Materialized views
  - Rich indexing
  - Time-series optimized

### Visualization
- **Apache Superset 3.1.0**
  - Rich chart library
  - SQL Lab
  - Real-time dashboards
  - Alert system

### Programming
- **Python 3.11** (Producer, Kafka Consumer)
- **Python 3.9** (Spark Processor - for Java 11 compatibility)
  - Modern async support
  - Type hints
  - Performance improvements

## Data Models

### Real-time Stream (Kafka Message)
```json
{
  "symbol": "BTCUSDT",
  "price": 43521.50,
  "timestamp": 1697654321000,
  "event_time": "2024-10-18T12:45:21.000Z",
  "volume": 1.234,
  "high": 43550.00,
  "low": 43500.00,
  "open": 43510.00,
  "trades": 1523
}
```

### Real-time Table (PostgreSQL)
```sql
CREATE TABLE stock.real_time_prices (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    price DECIMAL(20, 8) NOT NULL,
    timestamp BIGINT NOT NULL,
    event_time TIMESTAMP NOT NULL,
    volume DECIMAL(20, 8),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Aggregated Table (PostgreSQL)
```sql
CREATE TABLE stock.aggregated_prices_1min (
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
    UNIQUE(symbol, window_start)
);
```

## Scalability

### Horizontal Scaling

1. **Kafka Partitions**: Increase partitions for parallel processing
2. **Kafka Consumers**: Add more consumer instances for higher throughput
3. **Spark Workers**: Scale workers for faster batch processing

### Vertical Scaling

1. **Increase container memory limits**
2. **Allocate more CPU cores**
3. **Optimize PostgreSQL configuration**

## Fault Tolerance

### Data Persistence
- All data stored in Docker volumes
- Survives container restarts
- Backup-friendly architecture

### Processing Guarantees
- **Kafka**: At-least-once delivery
- **Kafka Consumer**: At-least-once processing with manual offset commits
- **Spark**: Fault-tolerant batch processing with retries

### High Availability
- Kafka: Replication factor (configurable)
- PostgreSQL: Point-in-time recovery
- Kafka Consumer: Consumer group coordination for failover

## Security Considerations

### Current Setup (Development)
- Default passwords (change for production)
- No TLS/SSL encryption
- Open network access

### Production Recommendations
1. Use environment variables for secrets
2. Enable SSL for PostgreSQL
3. Configure Kafka SASL authentication
4. Use reverse proxy for Superset
5. Implement network policies
6. Enable container security scanning

## Performance Characteristics

### Latency
- **Producer → Kafka**: < 100ms
- **Kafka → Flink → PostgreSQL**: < 500ms
- **End-to-end**: < 1 second

### Throughput
- **Kafka**: 10,000+ messages/second
- **Flink**: 5,000+ inserts/second
- **Spark**: Batch of 60,000 records/minute

### Storage
- **Real-time data**: ~1GB per day (5 symbols)
- **Aggregated data**: ~100MB per day
- **PostgreSQL total**: ~30GB per month

## Monitoring Points

### Application Metrics
- Producer: Messages sent per second
- Kafka: Consumer lag
- Flink: Records processed, checkpoints
- Spark: Batch duration, records processed
- PostgreSQL: Table sizes, query performance

### Infrastructure Metrics
- CPU usage per container
- Memory consumption
- Disk I/O
- Network throughput

### Access Dashboards
- Flink UI: http://localhost:8081
- Spark UI: http://localhost:8080
- Superset: http://localhost:8088
