# Frontend Setup Guide

## Overview

A beautiful, modern React frontend has been created for the Hiking Trip Organizer. The frontend provides an intuitive interface for users to:

1. **Select a region** (Lake District or Cornwall)
2. **Generate a hiking itinerary** with a single click
3. **View the route on an interactive map** with Leaflet
4. **See detailed day-by-day breakdowns** including:
   - Start and end points
   - Distance and duration
   - Scenic highlights
   - Terrain breakdown (mountain, forest, coastal, valley)

## Quick Start

### 1. Navigate to the frontend directory

```bash
cd /Users/edjohn/Documents/hiking-trip-organizer/frontend
```

### 2. Install dependencies (if not already done)

```bash
npm install
```

### 3. Start the backend API

In a separate terminal, ensure the Flask backend is running:

```bash
cd /Users/edjohn/Documents/hiking-trip-organizer
source venv/bin/activate
python app.py
```

And the Redis worker:

```bash
cd /Users/edjohn/Documents/hiking-trip-organizer
source venv/bin/activate
python worker.py
```

### 4. Start the frontend development server

```bash
cd /Users/edjohn/Documents/hiking-trip-organizer/frontend
npm start
```

The app will open at [http://localhost:3000](http://localhost:3000)

## Architecture

### Frontend Stack

- **React 18** with TypeScript for type safety
- **Tailwind CSS** for modern, responsive styling
- **Leaflet** for interactive mapping
- **Axios** for API communication
- **Lucide React** for beautiful icons

### Component Structure

```
src/
├── components/
│   ├── RegionSelector.tsx      # Region selection UI with cards
│   ├── RouteMap.tsx            # Interactive Leaflet map with markers
│   ├── DayDetails.tsx          # Day-by-day hiking information
│   └── LoadingSpinner.tsx      # Loading state with animation
├── services/
│   └── api.ts                  # Backend API integration
├── types.ts                    # TypeScript type definitions
├── App.tsx                     # Main application component
└── index.css                   # Global Tailwind styles
```

## Features

### 1. Region Selection
- Visual cards for Lake District and Cornwall
- Icons representing each region type (Mountain/Waves)
- Clear descriptions of each region

### 2. Route Generation
- Background job processing with RQ/Redis
- Real-time status polling
- Loading states with spinner animation
- Error handling and user feedback

### 3. Interactive Map
- Leaflet-based interactive map
- Color-coded markers for waypoints (blue) and scenic points (red)
- Route paths showing the hiking trail
- Popup information on marker clicks
- Auto-fitting bounds to show entire route

### 4. Daily Itinerary Display
- Summary cards showing:
  - Total distance
  - Total duration
  - Number of days
- Day-by-day cards with:
  - Start/end locations
  - Distance and time
  - Scenic highlights
  - Terrain breakdown visualization

### 5. Terrain Breakdown
- Visual progress bars showing terrain composition:
  - Mountain (grey)
  - Forest (green)
  - Coastal (blue)
  - Valley (yellow)
- Percentage-based representation
- Icons for each terrain type

## API Integration

The frontend communicates with the Flask backend through these endpoints:

### Get Regions
```
GET /api/regions
```
Returns available hiking regions with metadata.

### Generate Route
```
POST /api/{region}/generate-interactive-route
```
Starts background job to generate a route. Returns a job ID.

### Check Status
```
GET /api/{region}/route-status/{jobId}
```
Polls job status and returns route data when complete.

## Environment Configuration

Create or update `.env` file:

```env
REACT_APP_API_URL=http://localhost:5000
```

For production, update to your deployed API URL.

## Building for Production

```bash
npm run build
```

This creates an optimized production build in the `build/` directory.

## Deployment Options

### With Backend (Heroku)
1. Deploy backend with Flask + Redis
2. Build frontend: `npm run build`
3. Serve frontend static files from Flask or use a CDN

### Separate Frontend (Netlify/Vercel)
1. Connect repository to Netlify/Vercel
2. Set build command: `npm run build`
3. Set publish directory: `build`
4. Add environment variable: `REACT_APP_API_URL` pointing to your backend

## Customization

### Adding New Regions

1. **Backend**: Add region to `/api/regions` endpoint
2. **Frontend**: Update icon mapping in `RegionSelector.tsx`:
   ```typescript
   const getRegionIcon = (regionId: string) => {
     switch (regionId) {
       case 'your_region':
         return <YourIcon className="w-12 h-12" />;
       // ...
     }
   };
   ```

### Styling Changes

Modify `tailwind.config.js` for theme customization:

```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: {
          // Your custom colors
        },
      },
    },
  },
}
```

### Map Customization

In `RouteMap.tsx`, you can:
- Change tile provider (OpenStreetMap, Mapbox, etc.)
- Customize marker icons
- Adjust popup styling
- Modify route line colors and weights

## Troubleshooting

### Map not displaying
- Ensure Leaflet CSS is loaded in `public/index.html`
- Check browser console for errors
- Verify GeoJSON data structure

### Route generation stuck
- Check backend API is running
- Verify Redis is running
- Check network tab for API errors
- Ensure job queue is processing (run `python worker.py`)

### CORS errors
- Ensure Flask-CORS is configured
- Check `CORS(app)` is called in `app.py`
- Verify API URL in `.env` is correct

## Next Steps

1. **Add Authentication** - Integrate user accounts
2. **Save Routes** - Allow users to save favorite routes
3. **Share Routes** - Generate shareable links
4. **Export GPX** - Download routes for GPS devices
5. **Weather Integration** - Show forecast for hiking days
6. **Difficulty Ratings** - Add route difficulty indicators

## Screenshots

The frontend includes:
- 🏔️ Beautiful gradient backgrounds
- 🗺️ Interactive Leaflet maps with custom markers
- 📊 Visual terrain breakdowns with progress bars
- 📱 Fully responsive design for mobile/tablet/desktop
- ⚡ Loading states and error handling
- 🎨 Modern card-based UI with Tailwind CSS

Enjoy your hiking adventures! 🥾

