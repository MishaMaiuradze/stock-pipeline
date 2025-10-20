# Project Structure

```
stock-pipeline/
│
├── docker-compose.yml              # Main orchestration file
├── .env.example                    # Environment variables template
├── .gitignore                      # Git ignore file
├── README.md                       # Main documentation
├── SUPERSET_GUIDE.md              # Superset setup guide
│
├── start.sh                        # Start all services
├── stop.sh                         # Stop all services
├── check-setup.sh                  # Verify project setup
├── monitor.sh                      # Monitor service health
├── queries.sql                     # Sample PostgreSQL queries
│
├── init-scripts/                   # PostgreSQL initialization
│   └── 01_create_tables.sql       # Database schema
│
├── producer/                       # Binance data producer
│   ├── Dockerfile
│   ├── requirements.txt
│   └── producer.py                # WebSocket client
│
├── flink-processor/               # Flink stream processor
│   ├── Dockerfile
│   ├── requirements.txt
│   └── flink_processor.py         # Real-time processing
│
└── spark-processor/               # Spark batch processor
    ├── Dockerfile
    └── spark_processor.py         # Batch aggregation
```

## Component Descriptions

### Core Services

1. **Kafka** - Message broker (KRaft mode)
2. **PostgreSQL** - Data storage
3. **Flink** - Stream processing (JobManager + TaskManager)
4. **Spark** - Batch processing (Master + Worker)
5. **Superset** - Visualization and dashboards

### Python Applications

1. **producer.py** - Connects to Binance WebSocket, streams to Kafka
2. **flink_processor.py** - Consumes Kafka, writes raw data to PostgreSQL
3. **spark_processor.py** - Aggregates data, creates OHLC candles

### Configuration Files

1. **docker-compose.yml** - Service definitions and networking
2. **01_create_tables.sql** - Database schema and indexes
3. **.env.example** - Configuration template

### Utility Scripts

1. **start.sh** - Launch entire pipeline
2. **stop.sh** - Shutdown pipeline
3. **check-setup.sh** - Validate project files
4. **monitor.sh** - Check service health and data flow
5. **queries.sql** - Sample queries for analysis
