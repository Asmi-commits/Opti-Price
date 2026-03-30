#!/bin/bash
set -e

echo "=== Checking if data exists ==="
if [ ! -f "data/raw/sales_data.csv" ]; then
    echo "=== Generating dataset (first run) ==="
    python generate_data.py
    echo "=== Data generation complete ==="
else
    echo "=== Data already exists, skipping generation ==="
fi

echo "=== Starting API server ==="
exec uvicorn src.api.app:app --host 0.0.0.0 --port ${PORT:-8000}