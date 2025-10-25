# Data Flow Explained

## 🎯 The Real Architecture (Not What the Old Diagram Showed)

You were **absolutely correct** in your observation! The architecture diagram was misleading about how Spark gets its data.

---

## ❌ What the OLD diagram showed (WRONG)

```
Kafka → Kafka Consumer → PostgreSQL
     ↘
       Spark Processor → PostgreSQL
```

**This implied:** Spark reads directly from Kafka in parallel with the Kafka Consumer.

---

## ✅ What ACTUALLY happens (CORRECT)

```
Kafka → Kafka Consumer → PostgreSQL (real_time_prices table)
                              ↓
                         Spark reads from PostgreSQL
                              ↓
                         Spark creates aggregations
                              ↓
                    Spark writes back to PostgreSQL
```

**Reality:** Spark reads from PostgreSQL's `real_time_prices` table, NOT from Kafka!

---

## 📊 Step-by-Step Data Flow

### 1️⃣ **Binance Producer** (WebSocket → Kafka)
```python
# Receives real-time price updates
Binance WebSocket → Producer → Kafka Topic (binance-prices)
```

**Data Format:**
```json
{
  "symbol": "BTCUSDT",
  "price": 43521.50,
  "timestamp": 1697654321000,
  "event_time": "2024-10-18T12:45:21.000Z",
  "volume": 1.234
}
```

---

### 2️⃣ **Kafka Consumer** (Kafka → PostgreSQL)
```python
# Reads from Kafka and writes to PostgreSQL
Kafka Topic → Kafka Consumer → PostgreSQL (stock.real_time_prices)
```

**Code Evidence** (`kafka-consumer/kafka_consumer.py`):
```python
def process_message(self, message):
    """Process a single Kafka message and store it in PostgreSQL"""
    cursor = self.conn.cursor()
    
    cursor.execute("""
        INSERT INTO stock.real_time_prices 
        (symbol, price, timestamp, event_time, volume)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        message['symbol'],
        message['price'],
        message['timestamp'],
        message['event_time'],
        message.get('volume', 0)
    ))
    
    self.conn.commit()
```

**Result:** Real-time prices stored in `real_time_prices` table.

---

### 3️⃣ **Spark Processor** (PostgreSQL → Aggregations → PostgreSQL)

#### Step A: Read from PostgreSQL
```python
# spark-processor/spark_processor.py
def read_real_time_data(self, start_time, end_time):
    """Read real-time data from PostgreSQL"""
    query = f"""
        (SELECT symbol, price, timestamp, event_time, volume
         FROM stock.real_time_prices
         WHERE event_time >= '{start_time}'
         AND event_time < '{end_time}'
        ) as real_time_data
    """
    
    df = self.spark.read \
        .jdbc(url=JDBC_URL, table=query, properties=CONNECTION_PROPERTIES)
    
    return df
```

**Key Point:** Spark uses **JDBC** to read from PostgreSQL's `real_time_prices` table!

#### Step B: Create Aggregations
```python
def aggregate_1min(self, df):
    """Aggregate data into 1-minute windows"""
    agg_df = df_with_window.groupBy("symbol", "window_start", "window_end").agg(
        F.first("price").alias("open_price"),
        F.last("price").alias("close_price"),
        F.max("price").alias("high_price"),
        F.min("price").alias("low_price"),
        F.avg("price").alias("avg_price"),
        F.sum("volume").alias("total_volume"),
        F.count("*").alias("trade_count")
    )
    return agg_df
```

**Processing:**
- Reads last 10 minutes of data from PostgreSQL
- Creates 1-minute OHLC candles
- Creates 5-minute OHLC candles

#### Step C: Write Back to PostgreSQL
```python
def write_to_postgres(self, df, table_name):
    """Write aggregated data to PostgreSQL"""
    df.write \
        .jdbc(url=JDBC_URL, 
              table=table_name, 
              mode="append", 
              properties=CONNECTION_PROPERTIES)
```

**Result:** Aggregations stored in `aggregated_prices_1min` and `aggregated_prices_5min`.

---

### 4️⃣ **Apache Superset** (PostgreSQL → Dashboards)
```
PostgreSQL (all tables) → Superset → Real-time Dashboards
```

Superset queries all three tables:
- `real_time_prices` - For tick-by-tick data
- `aggregated_prices_1min` - For 1-minute candles
- `aggregated_prices_5min` - For 5-minute candles

---

## 🔍 Why This Architecture?

### Why doesn't Spark read from Kafka directly?

**Several reasons:**

1. **Simplicity**: Don't need Spark Structured Streaming complexity
2. **Replay capability**: Can re-aggregate historical data from PostgreSQL
3. **Lower resource usage**: Batch processing every 60 seconds vs continuous streaming
4. **Easier debugging**: Can query PostgreSQL to see what Spark will process
5. **Less Spark complexity**: Just batch jobs, no checkpointing/state management

### Trade-offs:

| Approach | Pros | Cons |
|----------|------|------|
| **Current (PostgreSQL)** | ✅ Simpler<br>✅ Can reprocess history<br>✅ Lower resources | ❌ Slight delay (up to 60s)<br>❌ Extra PostgreSQL load |
| **Alternative (Kafka)** | ✅ Lower latency<br>✅ True streaming | ❌ More complex<br>❌ Harder to replay<br>❌ Higher resource usage |

For a stock price aggregation pipeline, the current approach is perfect! 60-second batch windows are fine for OHLC candles.

---

## 📈 Data Latency Breakdown

```
Binance API → Producer: ~100ms
Producer → Kafka: ~10ms
Kafka → Consumer: ~50ms
Consumer → PostgreSQL: ~20ms
═══════════════════════════════
Real-time data latency: ~180ms ✅

PostgreSQL → Spark: Every 60 seconds
Spark Processing: ~5-10 seconds
Spark → PostgreSQL: ~2 seconds
═══════════════════════════════
Aggregation latency: 60-70 seconds ✅
```

**Key Insight:** Real-time data is fast (~180ms), aggregations run every minute.

---

## 🔄 Processing Timeline

```
Time    | Kafka Consumer              | Spark Processor
--------|----------------------------|---------------------------
00:00   | Consuming real-time data   | Reading PostgreSQL
00:01   | Consuming real-time data   | Creating 1-min aggregations
00:02   | Consuming real-time data   | Writing to PostgreSQL
00:03   | Consuming real-time data   | Sleeping...
...     | ...                        | ...
01:00   | Consuming real-time data   | Reading PostgreSQL again
```

**Both processes run continuously and independently!**

---

## 🎯 What This Means for You

### To add more symbols:
1. Edit `.env` → `BINANCE_SYMBOLS=BTCUSDT,ETHUSDT,...`
2. Restart: `docker-compose restart binance-producer`
3. **That's it!** Kafka Consumer will store them, Spark will aggregate them.

### To change aggregation windows:
1. Edit `spark-processor/spark_processor.py`
2. Add new aggregation function (e.g., `aggregate_15min`)
3. Restart: `docker-compose restart spark-processor`

### To reprocess historical data:
```bash
# Spark can re-read PostgreSQL and recreate aggregations!
# Just clear aggregation tables and let Spark run
docker exec postgres psql -U admin -d stock_data -c "TRUNCATE stock.aggregated_prices_1min;"
docker exec postgres psql -U admin -d stock_data -c "TRUNCATE stock.aggregated_prices_5min;"

# Spark will regenerate from real_time_prices on next run
```

---

## 🏗️ Architecture Summary

```
┌──────────────────────────────────────────────────────────┐
│                    REAL-TIME PATH                        │
├──────────────────────────────────────────────────────────┤
│ Binance → Producer → Kafka → Consumer → PostgreSQL      │
│                                           (180ms)        │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│                   AGGREGATION PATH                       │
├──────────────────────────────────────────────────────────┤
│ PostgreSQL → Spark → Aggregations → PostgreSQL          │
│  (real_time)         (1-min, 5-min)   (aggregated)      │
│              (runs every 60 seconds)                     │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│                  VISUALIZATION PATH                      │
├──────────────────────────────────────────────────────────┤
│ PostgreSQL → Superset → Dashboards                       │
│ (all tables)                                             │
└──────────────────────────────────────────────────────────┘
```

---

## ✅ Verification

Want to see the actual data flow? Run these commands:

```bash
# 1. Check what's in Kafka
docker exec kafka /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic binance-prices \
  --from-beginning --max-messages 5

# 2. Check what Kafka Consumer wrote to PostgreSQL
docker exec postgres psql -U admin -d stock_data -c \
  "SELECT symbol, price, event_time FROM stock.real_time_prices ORDER BY event_time DESC LIMIT 5;"

# 3. Check what Spark created
docker exec postgres psql -U admin -d stock_data -c \
  "SELECT symbol, window_start, open_price, close_price 
   FROM stock.aggregated_prices_1min 
   ORDER BY window_start DESC LIMIT 5;"

# 4. Watch Spark logs to see it reading from PostgreSQL
docker logs spark-processor --tail 20
# Look for: "Processing data from..." and "Reading real-time data"
```

---

## 🎓 Summary

**You were 100% correct!** 🎯

- ✅ Spark reads from PostgreSQL, NOT from Kafka
- ✅ Kafka Consumer is the only service reading from Kafka
- ✅ Spark processes batch data every 60 seconds
- ✅ Architecture diagram has been corrected

**The fixed architecture diagram now accurately shows:**
- Kafka → Kafka Consumer → PostgreSQL (real-time path)
- PostgreSQL → Spark → PostgreSQL (aggregation path)
- PostgreSQL → Superset (visualization path)

Great catch! This is exactly the kind of attention to detail that leads to better understanding and documentation! 🚀
