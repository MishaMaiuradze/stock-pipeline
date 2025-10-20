# Quick Start Guide

## Prerequisites
- Docker and Docker Compose installed
- 8GB+ RAM available
- Ports available: 5432, 8080, 8081, 8088, 9092

## Installation (5 minutes)

### Step 1: Verify Setup
```bash
cd /home/admin/dev_env/stock-pipeline
./check-setup.sh
```

### Step 2: Start Services
```bash
./start.sh
```

This will:
- ✓ Start Kafka (no Zookeeper needed)
- ✓ Initialize PostgreSQL with schema
- ✓ Start Flink JobManager and TaskManager
- ✓ Start Spark Master and Worker
- ✓ Launch Binance producer (starts streaming immediately)
- ✓ Start Flink processor (real-time writes to DB)
- ✓ Start Spark processor (batch aggregation)
- ✓ Start Superset dashboard

### Step 3: Wait for Initialization
Services will be ready in about 60 seconds. Monitor with:
```bash
./monitor.sh
```

### Step 4: Access Dashboards

#### Superset (Main Dashboard)
- URL: http://localhost:8088
- Username: `admin`
- Password: `admin123`

#### Flink Dashboard
- URL: http://localhost:8081

#### Spark Dashboard
- URL: http://localhost:8080

### Step 5: Verify Data Flow

Connect to PostgreSQL:
```bash
docker exec -it postgres psql -U admin -d stock_data
```

Run a query:
```sql
-- Check latest prices
SELECT * FROM stock.latest_prices;

-- Count records
SELECT symbol, COUNT(*) FROM stock.real_time_prices 
GROUP BY symbol;
```

Exit: `\q`

## Configuration

### Change Trading Symbols
Edit `docker-compose.yml`:
```yaml
binance-producer:
  environment:
    BINANCE_SYMBOLS: BTCUSDT,ETHUSDT,BNBUSDT,XRPUSDT,ADAUSDT
```

Restart:
```bash
docker-compose restart binance-producer
```

### Adjust Aggregation Frequency
Edit `spark-processor/spark_processor.py`, change line:
```python
time.sleep(60)  # Change to 300 for 5-minute batches
```

Rebuild and restart:
```bash
docker-compose up -d --build spark-processor
```

## Common Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f binance-producer
docker-compose logs -f flink-processor
docker-compose logs -f spark-processor
```

### Monitor Health
```bash
./monitor.sh
```

### Restart Service
```bash
docker-compose restart <service-name>
```

### Stop Everything
```bash
./stop.sh
```

### Stop and Remove All Data
```bash
docker-compose down -v  # WARNING: Deletes all data!
```

## Data Persistence

All data is stored in Docker volumes:
- `kafka-data` - Kafka messages
- `postgres-data` - All database data
- `flink-checkpoints` - Flink state
- `spark-apps` - Spark applications
- `superset-data` - Superset config

**Data survives container restarts!**

## Troubleshooting

### No data appearing
1. Check producer logs: `docker-compose logs binance-producer`
2. Verify Kafka topic: `docker exec kafka kafka-topics.sh --list --bootstrap-server localhost:9092`
3. Check database: `docker exec -it postgres psql -U admin -d stock_data -c "SELECT COUNT(*) FROM stock.real_time_prices;"`

### Service won't start
1. Check ports are available: `netstat -tuln | grep -E '5432|8080|8081|8088|9092'`
2. Check logs: `docker-compose logs <service-name>`
3. Restart: `docker-compose restart <service-name>`

### Out of memory
1. Stop services: `./stop.sh`
2. Edit `docker-compose.yml` to reduce worker memory
3. Restart: `./start.sh`

### Kafka connection refused
Wait 30 seconds after starting for Kafka to fully initialize.

## Next Steps

1. **Set up Superset Dashboard** - Follow `SUPERSET_GUIDE.md`
2. **Explore Data** - Use queries from `queries.sql`
3. **Monitor Performance** - Check Flink and Spark dashboards
4. **Customize** - Add more symbols or change aggregation windows

## Performance Tips

1. **For high-volume trading:**
   ```yaml
   kafka:
     environment:
       KAFKA_NUM_PARTITIONS: 6
   ```

2. **Scale Spark workers:**
   ```bash
   docker-compose up -d --scale spark-worker=3
   ```

3. **Optimize PostgreSQL:**
   - Add more indexes for frequently queried columns
   - Tune `shared_buffers` in PostgreSQL config

## Support

Check these files for more information:
- `README.md` - Complete documentation
- `SUPERSET_GUIDE.md` - Dashboard setup
- `queries.sql` - Sample queries
- `PROJECT_STRUCTURE.md` - Architecture details

Enjoy your real-time cryptocurrency tracking system! 🚀
