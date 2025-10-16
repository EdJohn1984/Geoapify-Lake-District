#!/bin/bash

# Hiking Trip Organizer - Application Startup Script

echo "🏔️  Starting Hiking Trip Organizer..."
echo "======================================"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Redis is running
if ! pgrep "redis-server" > /dev/null; then
    echo -e "${RED}❌ Redis is not running${NC}"
    echo "Please start Redis with: redis-server"
    exit 1
fi

echo -e "${GREEN}✅ Redis is running${NC}"

# Activate virtual environment
echo -e "${BLUE}📦 Activating Python virtual environment...${NC}"
source venv/bin/activate

# Start Flask backend in background
echo -e "${BLUE}🚀 Starting Flask backend API...${NC}"
OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES python app.py > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}✅ Backend started (PID: $BACKEND_PID)${NC}"

# Start RQ worker in background
echo -e "${BLUE}⚙️  Starting RQ worker...${NC}"
OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES python worker.py > logs/worker.log 2>&1 &
WORKER_PID=$!
echo -e "${GREEN}✅ Worker started (PID: $WORKER_PID)${NC}"

# Wait a moment for backend to initialize
sleep 2

# Start React frontend
echo -e "${BLUE}🎨 Starting React frontend...${NC}"
cd frontend
npm start &
FRONTEND_PID=$!

echo ""
echo -e "${GREEN}======================================"
echo "✅ All services started successfully!"
echo "======================================${NC}"
echo ""
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:5000"
echo ""
echo "Process IDs:"
echo "  - Backend: $BACKEND_PID"
echo "  - Worker: $WORKER_PID"
echo "  - Frontend: $FRONTEND_PID"
echo ""
echo -e "${BLUE}To stop all services, run: ./stop-app.sh${NC}"
echo ""

# Save PIDs to file for cleanup
echo "$BACKEND_PID" > .pids
echo "$WORKER_PID" >> .pids
echo "$FRONTEND_PID" >> .pids

