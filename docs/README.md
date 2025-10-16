# Hiking Trip Organizer

A beautiful web application for planning multi-day hiking adventures with intelligent route generation, interactive maps, and detailed itineraries. Built with Flask (Python) and React (TypeScript).

## ✨ Features

### Route Planning
- **Region Selection**: Choose between Lake District and Cornwall hiking routes
- **Intelligent Route Generation**: AI-powered route optimization with scenic point integration
- **Interactive Maps**: Visualize your complete hiking route with Leaflet maps
- **3-Day Itineraries**: Automatically generated multi-day hiking adventures

### Day-by-Day Details
- **Start/End Points**: Clear waypoint information for each day
- **Distance & Duration**: Accurate hiking metrics
- **Scenic Highlights**: Notable peaks, views, and landmarks along the route
- **Terrain Breakdown**: Visual analysis of terrain types (mountain, forest, coastal, valley)

### Technology
- **Background Processing**: Asynchronous route generation with Redis/RQ
- **GeoJSON Export**: Standards-based geographic data format
- **Real-time Updates**: Live job status polling
- **Responsive Design**: Works seamlessly on mobile, tablet, and desktop

## 🛠️ Tech Stack

### Backend
- **Flask** - Python web framework
- **Redis & RQ** - Background job processing
- **Flask-CORS** - Cross-origin resource sharing
- **Geoapify API** - Route planning and geocoding
- **OpenStreetMap** - Terrain and surface data
- **Gunicorn** - Production WSGI server

### Frontend
- **React 18** - UI framework with TypeScript
- **Tailwind CSS** - Modern utility-first styling
- **Leaflet & React-Leaflet** - Interactive mapping
- **Axios** - HTTP client
- **Lucide React** - Beautiful icon library

### Data & APIs
- **GeoJSON** - Geographic data format
- **OpenStreetMap Overpass API** - Terrain analysis
- **Scenic Points Database** - Peak and landmark data

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- Redis (for background job processing)
- npm or yarn

### Easy Startup (Recommended)

1. **Install Redis** (if not already installed):
   ```bash
   # macOS
   brew install redis
   brew services start redis
   
   # Ubuntu/Debian
   sudo apt-get install redis-server
   sudo systemctl start redis
   ```

2. **Install Backend Dependencies**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Install Frontend Dependencies**:
   ```bash
   cd frontend
   npm install
   cd ..
   ```

4. **Start Everything**:
   ```bash
   ./start-app.sh
   ```

   This will start:
   - Flask backend API (http://localhost:5000)
   - RQ worker for background jobs
   - React frontend (http://localhost:3000)

5. **Open your browser** to [http://localhost:3000](http://localhost:3000)

### Manual Setup

#### Backend
```bash
# Activate virtual environment
source venv/bin/activate

# Start Flask API
python app.py

# In another terminal, start RQ worker
python worker.py
```

#### Frontend
```bash
cd frontend
npm start
```

### Stopping the Application
```bash
./stop-app.sh
```

## 📖 Usage

1. **Select a Region**: Choose between Lake District or Cornwall
2. **Generate Route**: Click "Generate Hiking Route" button
3. **View Results**:
   - See your route on an interactive map
   - Review day-by-day hiking details
   - Check terrain breakdowns and scenic highlights

## 🗺️ Available Regions

### Lake District
- Mountain hiking routes
- Scenic peaks and ridges
- 3-day itineraries with ~20km per day
- Famous peaks: Helvellyn, Great Rigg, Black Fell

### Cornwall
- Coastal and inland routes
- Dramatic coastline views
- 3-day itineraries with varied terrain
- Beach coves, cliffs, and fishing villages

## 📂 Project Structure

```
hiking-trip-organizer/
├── frontend/                  # React TypeScript frontend
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── services/         # API integration
│   │   └── types.ts          # TypeScript definitions
│   └── package.json
├── app.py                    # Flask API server
├── route_tasks.py           # Background job functions
├── geoapify_planner.py      # Lake District route planner
├── cornwall_planner.py      # Cornwall route planner
├── worker.py                # RQ worker
├── cache/                   # Cached scenic points
├── requirements.txt         # Python dependencies
├── start-app.sh            # Startup script
└── stop-app.sh             # Shutdown script
```

## 🔧 API Endpoints

### Regions
- `GET /api/regions` - List available regions

### Lake District
- `POST /api/generate-interactive-route` - Generate route
- `GET /api/route-status/<job_id>` - Check status

### Cornwall
- `POST /api/cornwall/generate-interactive-route` - Generate route
- `GET /api/cornwall/route-status/<job_id>` - Check status

## 🚢 Deployment

### Heroku (Recommended)

1. **Create Heroku app**:
   ```bash
   heroku create your-app-name
   heroku addons:create heroku-redis:mini
   ```

2. **Deploy backend**:
   ```bash
   git push heroku main
   ```

3. **Scale workers**:
   ```bash
   heroku ps:scale web=1 worker=1
   ```

4. **Build & deploy frontend**:
   ```bash
   cd frontend
   npm run build
   # Serve from Flask or deploy to Netlify/Vercel
   ```

### Alternative: Separate Deployments

- **Backend**: Heroku, Railway, or DigitalOcean
- **Frontend**: Netlify, Vercel, or Cloudflare Pages

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 