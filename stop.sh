#!/bin/bash

echo "Stopping Binance Stock Price Streaming Pipeline..."
echo "=================================================="
echo ""

docker-compose down

echo ""
echo "All services stopped."
echo ""
echo "Note: Data is preserved in Docker volumes."
echo "To completely remove all data, run:"
echo "  docker-compose down -v"
echo ""
