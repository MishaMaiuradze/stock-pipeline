#!/bin/bash

echo "Checking project structure..."
echo "=================================================="
echo ""

# Check if all required files exist
files=(
    "docker-compose.yml"
    "producer/Dockerfile"
    "producer/producer.py"
    "producer/requirements.txt"
    "flink-processor/Dockerfile"
    "flink-processor/flink_processor.py"
    "flink-processor/requirements.txt"
    "spark-processor/Dockerfile"
    "spark-processor/spark_processor.py"
    "init-scripts/01_create_tables.sql"
)

all_files_exist=true

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file"
    else
        echo "✗ $file (missing)"
        all_files_exist=false
    fi
done

echo ""

if [ "$all_files_exist" = true ]; then
    echo "✓ All required files are present!"
else
    echo "✗ Some files are missing. Please check the project structure."
    exit 1
fi

echo ""
echo "Checking Docker..."
if docker info > /dev/null 2>&1; then
    echo "✓ Docker is running"
else
    echo "✗ Docker is not running"
    exit 1
fi

echo ""
echo "Checking docker-compose..."
if command -v docker-compose &> /dev/null; then
    echo "✓ docker-compose is installed ($(docker-compose --version))"
else
    echo "✗ docker-compose is not installed"
    exit 1
fi

echo ""
echo "=================================================="
echo "Project is ready to launch!"
echo "Run ./start.sh to start the pipeline"
echo "=================================================="
