#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "=================================================="
echo "Binance Stock Pipeline - Service Monitor"
echo "=================================================="
echo ""

# Function to check service health
check_service() {
    local service=$1
    local health=$(docker inspect --format='{{.State.Health.Status}}' $service 2>/dev/null)
    local status=$(docker inspect --format='{{.State.Status}}' $service 2>/dev/null)
    
    if [ "$status" = "running" ]; then
        if [ "$health" = "healthy" ]; then
            echo -e "${GREEN}✓${NC} $service: running (healthy)"
        elif [ "$health" = "unhealthy" ]; then
            echo -e "${RED}✗${NC} $service: running (unhealthy)"
        else
            echo -e "${YELLOW}⚠${NC} $service: running (no health check)"
        fi
    else
        echo -e "${RED}✗${NC} $service: $status"
    fi
}

# Check all services
echo "Service Status:"
echo "--------------------------------------------------"
check_service "kafka"
check_service "postgres"
check_service "spark-master"
check_service "spark-worker"
check_service "binance-producer"
check_service "kafka-consumer"
check_service "spark-processor"
check_service "superset"

echo ""
echo "Data Flow Check:"
echo "--------------------------------------------------"

# Check Kafka topic
echo -n "Kafka topic 'binance-prices': "
topic_exists=$(docker exec kafka kafka-topics.sh --list --bootstrap-server localhost:9092 2>/dev/null | grep -c "binance-prices")
if [ "$topic_exists" -gt 0 ]; then
    echo -e "${GREEN}✓ exists${NC}"
    
    # Get message count (approximate)
    echo -n "  Recent messages: "
    docker exec kafka kafka-run-class.sh kafka.tools.GetOffsetShell --broker-list localhost:9092 --topic binance-prices --time -1 2>/dev/null | awk -F ":" '{sum += $3} END {print sum}'
else
    echo -e "${RED}✗ not found${NC}"
fi

# Check PostgreSQL tables
echo -n "PostgreSQL tables: "
table_count=$(docker exec postgres psql -U admin -d stock_data -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'stock';" 2>/dev/null | tr -d ' ')
if [ "$table_count" -gt 0 ]; then
    echo -e "${GREEN}✓ $table_count tables${NC}"
    
    # Check record counts
    echo "  Table record counts:"
    docker exec postgres psql -U admin -d stock_data -t -c "
        SELECT '    ' || table_name || ': ' || 
               (xpath('/row/count/text()', xml_count))[1]::text::int AS row_count
        FROM (
            SELECT table_name, 
                   query_to_xml(format('SELECT COUNT(*) AS count FROM stock.%I', table_name), false, true, '') AS xml_count
            FROM information_schema.tables
            WHERE table_schema = 'stock' AND table_type = 'BASE TABLE'
        ) t;" 2>/dev/null
else
    echo -e "${RED}✗ no tables found${NC}"
fi

echo ""
echo "Container Resource Usage:"
echo "--------------------------------------------------"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | head -11

echo ""
echo "=================================================="
echo "Quick Actions:"
echo "=================================================="
echo "View producer logs:    docker-compose logs -f binance-producer"
echo "View consumer logs:    docker-compose logs -f kafka-consumer"
echo "View Spark logs:       docker-compose logs -f spark-processor"
echo "Restart all:           docker-compose restart"
echo "Stop all:              ./stop.sh"
echo ""
