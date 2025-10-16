# 🚀 Quick Start Guide

## Get Up and Running in 5 Minutes

### Prerequisites Check
```bash
# Check Python (need 3.9+)
python --version

# Check Node.js (need 16+)
node --version

# Check Redis
redis-cli ping  # Should return PONG
```

If Redis is not installed:
```bash
# macOS
brew install redis && brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server && sudo systemctl start redis
```

### Installation

1. **Clone & Navigate**
   ```bash
   cd /Users/edjohn/Documents/hiking-trip-organizer
   ```

2. **Backend Setup** (if not done)
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Frontend Setup** (if not done)
   ```bash
   cd frontend
   npm install
   cd ..
   ```

### Running the App

**Option 1: Easy Start (Recommended)**
```bash
./start-app.sh
```

**Option 2: Manual Start**
```bash
# Terminal 1: Backend
source venv/bin/activate && python app.py

# Terminal 2: Worker  
source venv/bin/activate && python worker.py

# Terminal 3: Frontend
cd frontend && npm start
```

### Access the App
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000

### Stopping the App
```bash
./stop-app.sh
```

## 📱 How to Use

1. **Select a Region**
   - Choose Lake District (mountains) or Cornwall (coast)

2. **Generate Route**
   - Click the "Generate Hiking Route" button
   - Wait 10-30 seconds for route generation

3. **Explore Results**
   - View interactive map with your route
   - Check day-by-day hiking details
   - See terrain breakdown for each day

## 🎯 What You'll See

### Region Selection
Two beautiful cards with region options and descriptions

### Loading State
Animated spinner while route is being generated

### Results Display
- **Map**: Interactive Leaflet map with markers and route path
- **Summary**: Total distance, duration, and days
- **Daily Details**: Cards for each day showing:
  - Start and end points
  - Distance and time
  - Scenic highlights
  - Terrain composition (mountain, forest, coastal, valley)

## 🆘 Troubleshooting

**Nothing happens when I click "Generate Route"?**
- Check backend is running: `curl http://localhost:5000/api/regions`
- Check Redis is running: `redis-cli ping`
- Check worker is running: `ps aux | grep worker.py`

**Map not showing?**
- Clear browser cache
- Check browser console for errors
- Verify Leaflet CSS loaded in index.html

**CORS errors?**
- Ensure Flask-CORS is installed: `pip show flask-cors`
- Check CORS is enabled in app.py

## 📖 More Information

- **Full Setup**: See FRONTEND_SETUP.md
- **Demo Guide**: See DEMO_GUIDE.md  
- **Implementation**: See FRONTEND_COMPLETE.md

## 🎉 You're All Set!

Enjoy planning your hiking adventures! 🏔️

