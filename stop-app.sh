#!/bin/bash

# Hiking Trip Organizer - Application Shutdown Script

echo "🛑 Stopping Hiking Trip Organizer..."
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

if [ ! -f .pids ]; then
    echo -e "${RED}No PID file found. Services may not be running.${NC}"
    exit 1
fi

# Read PIDs and stop processes
while read pid; do
    if ps -p $pid > /dev/null 2>&1; then
        echo "Stopping process $pid..."
        kill $pid
    fi
done < .pids

# Clean up PID file
rm .pids

echo -e "${GREEN}======================================"
echo "✅ All services stopped successfully!"
echo "======================================${NC}"

