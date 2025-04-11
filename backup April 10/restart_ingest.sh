#!/bin/bash

echo "?? Restarting ingest_app on port 8000..."

# Kill existing uvicorn process on port 8000
pkill -f "uvicorn ingest_app:app --host 0.0.0.0 --port 8000"

# Navigate to project folder
cd ~/owntracks-backend || exit

# Activate virtual environment
source venv/bin/activate

# Restart with nohup
nohup uvicorn ingest_app:app --host 0.0.0.0 --port 8000 > ingest.log 2>&1 &

echo "? ingest_app restarted and running in background. Log: ingest.log"
