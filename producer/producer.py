#!/usr/bin/env python3
"""
Binance WebSocket Producer - Streams real-time price data to Kafka
"""
import json
import time
import logging
import os
from datetime import datetime
from kafka import KafkaProducer
from kafka.errors import KafkaError
import websocket
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'binance-prices')
BINANCE_SYMBOLS = os.getenv('BINANCE_SYMBOLS', 'BTCUSDT,ETHUSDT,BNBUSDT').split(',')

class BinanceProducer:
    def __init__(self):
        self.producer = None
        self.ws = None
        self.running = False
        self.connect_kafka()
        
    def connect_kafka(self):
        """Connect to Kafka with retry logic"""
        max_retries = 10
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                self.producer = KafkaProducer(
                    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    acks='all',
                    retries=3,
                    max_in_flight_requests_per_connection=1
                )
                logger.info(f"Connected to Kafka at {KAFKA_BOOTSTRAP_SERVERS}")
                return
            except KafkaError as e:
                logger.error(f"Kafka connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    raise
    
    def on_message(self, ws, message):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)
            
            # Handle stream format with 'data' wrapper
            if 'data' in data:
                data = data['data']
            
            # Extract relevant information
            symbol = data.get('s')
            if not symbol:
                return  # Skip if no symbol
                
            price = float(data.get('c', 0))  # Current price
            timestamp = data.get('E')  # Event time
            if not timestamp:
                timestamp = int(datetime.now().timestamp() * 1000)
            
            volume = float(data.get('v', 0))  # Volume
            
            # Prepare message for Kafka
            kafka_message = {
                'symbol': symbol,
                'price': price,
                'timestamp': timestamp,
                'event_time': datetime.fromtimestamp(timestamp / 1000).isoformat(),
                'volume': volume,
                'high': float(data.get('h', 0)),
                'low': float(data.get('l', 0)),
                'open': float(data.get('o', 0)),
                'trades': data.get('n', 0)
            }
            
            # Send to Kafka
            future = self.producer.send(KAFKA_TOPIC, value=kafka_message)
            future.get(timeout=10)
            
            logger.info(f"Sent: {symbol} @ ${price:.2f}")
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def on_error(self, ws, error):
        """Handle WebSocket errors"""
        logger.error(f"WebSocket error: {error}")
    
    def on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close"""
        logger.warning(f"WebSocket closed: {close_status_code} - {close_msg}")
        self.running = False
    
    def on_open(self, ws):
        """Handle WebSocket open"""
        logger.info("WebSocket connection opened")
        self.running = True
    
    def start_stream(self):
        """Start streaming data from Binance WebSocket"""
        # Create WebSocket URL for 24hr ticker stream
        streams = [f"{symbol.lower()}@ticker" for symbol in BINANCE_SYMBOLS]
        ws_url = f"wss://stream.binance.com:9443/stream?streams={'/'.join(streams)}"
        
        logger.info(f"Connecting to Binance WebSocket for symbols: {', '.join(BINANCE_SYMBOLS)}")
        
        while True:
            try:
                self.ws = websocket.WebSocketApp(
                    ws_url,
                    on_message=lambda ws, msg: self.on_message(ws, msg),
                    on_error=lambda ws, err: self.on_error(ws, err),
                    on_close=lambda ws, code, msg: self.on_close(ws, code, msg),
                    on_open=lambda ws: self.on_open(ws)
                )
                
                self.ws.run_forever()
                
                if not self.running:
                    logger.info("Reconnecting in 5 seconds...")
                    time.sleep(5)
                    
            except Exception as e:
                logger.error(f"Error in WebSocket stream: {e}")
                time.sleep(5)
    
    def close(self):
        """Clean up resources"""
        if self.ws:
            self.ws.close()
        if self.producer:
            self.producer.flush()
            self.producer.close()
        logger.info("Producer closed")

def main():
    logger.info("Starting Binance Producer...")
    producer = BinanceProducer()
    
    try:
        producer.start_stream()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        producer.close()

if __name__ == "__main__":
    main()
