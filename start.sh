#!/bin/bash

echo "Starting Binance Stock Price Streaming Pipeline..."
echo "=================================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "Error: docker-compose is not installed."
    exit 1
fi

echo "Building and starting containers..."
docker-compose up -d

echo ""
echo "Waiting for services to be ready..."
sleep 10

echo ""
echo "=================================================="
echo "Services Status:"
echo "=================================================="
docker-compose ps

echo ""
echo "=================================================="
echo "Access Points:"
echo "=================================================="
echo "📊 Superset Dashboard: http://localhost:8088"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "🔥 Flink Dashboard:    http://localhost:8081"
echo "⚡ Spark Dashboard:    http://localhost:8080"
echo ""
echo "🗄️  PostgreSQL:"
echo "   Host: localhost"
echo "   Port: 5432"
echo "   Database: stock_data"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "=================================================="
echo "Useful Commands:"
echo "=================================================="
echo "View all logs:        docker-compose logs -f"
echo "View producer logs:   docker-compose logs -f binance-producer"
echo "View Flink logs:      docker-compose logs -f flink-processor"
echo "View Spark logs:      docker-compose logs -f spark-processor"
echo "Stop all services:    docker-compose down"
echo ""
echo "To monitor data flow, check the logs:"
echo "docker-compose logs -f binance-producer flink-processor"
echo ""
