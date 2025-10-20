#!/usr/bin/env python3
"""
Flink Stream Processor - Processes Kafka stream and writes to PostgreSQL
"""
import json
import logging
import os
import time
from datetime import datetime
import psycopg2
from psycopg2 import pool
from kafka import KafkaConsumer
from kafka.errors import KafkaError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'binance-prices')
KAFKA_GROUP_ID = 'flink-processor-group'

POSTGRES_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'postgres'),
    'port': int(os.getenv('POSTGRES_PORT', 5432)),
    'database': os.getenv('POSTGRES_DB', 'stock_data'),
    'user': os.getenv('POSTGRES_USER', 'admin'),
    'password': os.getenv('POSTGRES_PASSWORD', 'admin123')
}

class FlinkProcessor:
    def __init__(self):
        self.consumer = None
        self.db_pool = None
        self.connect_postgres()
        self.connect_kafka()
        
    def connect_postgres(self):
        """Create PostgreSQL connection pool"""
        max_retries = 10
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                self.db_pool = pool.SimpleConnectionPool(
                    minconn=1,
                    maxconn=10,
                    **POSTGRES_CONFIG
                )
                logger.info("Connected to PostgreSQL")
                return
            except Exception as e:
                logger.error(f"PostgreSQL connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    raise
    
    def connect_kafka(self):
        """Connect to Kafka consumer"""
        max_retries = 10
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                self.consumer = KafkaConsumer(
                    KAFKA_TOPIC,
                    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                    group_id=KAFKA_GROUP_ID,
                    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                    auto_offset_reset='latest',
                    enable_auto_commit=True,
                    auto_commit_interval_ms=5000
                )
                logger.info(f"Connected to Kafka topic: {KAFKA_TOPIC}")
                return
            except KafkaError as e:
                logger.error(f"Kafka connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    raise
    
    def insert_price_data(self, data):
        """Insert price data into PostgreSQL"""
        conn = None
        try:
            conn = self.db_pool.getconn()
            cursor = conn.cursor()
            
            insert_query = """
                INSERT INTO stock.real_time_prices 
                (symbol, price, timestamp, event_time, volume)
                VALUES (%s, %s, %s, %s, %s)
            """
            
            # Parse event_time
            event_time = datetime.fromisoformat(data['event_time'])
            
            cursor.execute(insert_query, (
                data['symbol'],
                data['price'],
                data['timestamp'],
                event_time,
                data['volume']
            ))
            
            conn.commit()
            cursor.close()
            
            logger.info(f"Inserted: {data['symbol']} @ ${data['price']:.2f}")
            
        except Exception as e:
            logger.error(f"Error inserting data: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                self.db_pool.putconn(conn)
    
    def process_stream(self):
        """Process Kafka stream"""
        logger.info("Starting stream processing...")
        
        try:
            for message in self.consumer:
                try:
                    data = message.value
                    self.insert_price_data(data)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            self.close()
    
    def close(self):
        """Clean up resources"""
        if self.consumer:
            self.consumer.close()
        if self.db_pool:
            self.db_pool.closeall()
        logger.info("Processor closed")

def main():
    logger.info("Starting Flink Stream Processor...")
    
    # Wait a bit for services to be ready
    time.sleep(10)
    
    processor = FlinkProcessor()
    processor.process_stream()

if __name__ == "__main__":
    main()
