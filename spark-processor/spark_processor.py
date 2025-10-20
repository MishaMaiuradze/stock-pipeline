#!/usr/bin/env python3
"""
Spark Batch Processor - Aggregates data from PostgreSQL
"""
import os
import time
import logging
from datetime import datetime, timedelta
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
POSTGRES_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'postgres'),
    'port': os.getenv('POSTGRES_PORT', '5432'),
    'database': os.getenv('POSTGRES_DB', 'stock_data'),
    'user': os.getenv('POSTGRES_USER', 'admin'),
    'password': os.getenv('POSTGRES_PASSWORD', 'admin123')
}

JDBC_URL = f"jdbc:postgresql://{POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}/{POSTGRES_CONFIG['database']}"
CONNECTION_PROPERTIES = {
    "user": POSTGRES_CONFIG['user'],
    "password": POSTGRES_CONFIG['password'],
    "driver": "org.postgresql.Driver"
}

class SparkProcessor:
    def __init__(self):
        self.spark = self.create_spark_session()
        
    def create_spark_session(self):
        """Create Spark session"""
        logger.info("Creating Spark session...")
        
        spark = SparkSession.builder \
            .appName("BinanceStockAggregator") \
            .master("local[2]") \
            .config("spark.jars.packages", "org.postgresql:postgresql:42.7.1") \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .config("spark.ui.enabled", "false") \
            .config("spark.driver.memory", "1g") \
            .getOrCreate()
        
        spark.sparkContext.setLogLevel("ERROR")
        logger.info("Spark session created")
        return spark
    
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
    
    def aggregate_1min(self, df):
        """Aggregate data into 1-minute windows"""
        df_with_window = df.withColumn(
            "window_start",
            F.date_trunc("minute", F.col("event_time"))
        ).withColumn(
            "window_end",
            F.col("window_start") + F.expr("INTERVAL 1 MINUTE")
        )
        
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
    
    def aggregate_5min(self, df):
        """Aggregate data into 5-minute windows"""
        # Create 5-minute windows
        df_with_window = df.withColumn(
            "window_start",
            F.from_unixtime(
                (F.unix_timestamp("event_time") / 300).cast("long") * 300
            ).cast("timestamp")
        ).withColumn(
            "window_end",
            F.col("window_start") + F.expr("INTERVAL 5 MINUTES")
        )
        
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
    
    def write_to_postgres(self, df, table_name):
        """Write aggregated data to PostgreSQL"""
        try:
            df.write \
                .jdbc(url=JDBC_URL, 
                      table=table_name, 
                      mode="append", 
                      properties=CONNECTION_PROPERTIES)
            logger.info(f"Written {df.count()} records to {table_name}")
        except Exception as e:
            logger.error(f"Error writing to {table_name}: {e}")
    
    def process_batch(self):
        """Process a batch of data"""
        # Process last 10 minutes of data
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=10)
        
        logger.info(f"Processing data from {start_time} to {end_time}")
        
        try:
            # Read real-time data
            df = self.read_real_time_data(start_time, end_time)
            
            if df.count() == 0:
                logger.info("No data to process")
                return
            
            # Aggregate 1-minute data
            agg_1min = self.aggregate_1min(df)
            self.write_to_postgres(agg_1min, "stock.aggregated_prices_1min")
            
            # Aggregate 5-minute data
            agg_5min = self.aggregate_5min(df)
            self.write_to_postgres(agg_5min, "stock.aggregated_prices_5min")
            
            # Refresh materialized view
            self.refresh_materialized_view()
            
        except Exception as e:
            logger.error(f"Error processing batch: {e}")
    
    def refresh_materialized_view(self):
        """Refresh the latest prices materialized view"""
        try:
            import psycopg2
            conn = psycopg2.connect(**POSTGRES_CONFIG)
            cursor = conn.cursor()
            cursor.execute("REFRESH MATERIALIZED VIEW stock.latest_prices")
            conn.commit()
            cursor.close()
            conn.close()
            logger.info("Refreshed materialized view")
        except Exception as e:
            logger.error(f"Error refreshing materialized view: {e}")
    
    def run_continuous(self):
        """Run continuous processing"""
        logger.info("Starting continuous processing (every 1 minute)...")
        
        while True:
            try:
                self.process_batch()
                time.sleep(60)  # Wait 1 minute
            except KeyboardInterrupt:
                logger.info("Shutting down...")
                break
            except Exception as e:
                logger.error(f"Error in continuous processing: {e}")
                time.sleep(60)
    
    def stop(self):
        """Stop Spark session"""
        self.spark.stop()
        logger.info("Spark session stopped")

def main():
    logger.info("Starting Spark Batch Processor...")
    
    # Wait for services to be ready
    time.sleep(30)
    
    processor = SparkProcessor()
    
    try:
        processor.run_continuous()
    finally:
        processor.stop()

if __name__ == "__main__":
    main()
