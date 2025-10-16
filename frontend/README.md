# Hiking Trip Organizer - Frontend

A beautiful, modern React frontend for planning multi-day hiking adventures with interactive maps and detailed itineraries.

## Features

- **Region Selection**: Choose between Lake District and Cornwall hiking routes
- **Interactive Maps**: View your complete hiking route on an interactive Leaflet map
- **Day-by-Day Details**: See detailed information for each day including:
  - Start and end points
  - Distance and duration
  - Scenic highlights along the route
  - Terrain breakdown (mountain, forest, coastal, valley)
- **Responsive Design**: Works seamlessly on mobile, tablet, and desktop
- **Real-time Route Generation**: Background job processing with live status updates

## Tech Stack

- **React 18** with TypeScript
- **Tailwind CSS** for styling
- **Leaflet** & **React-Leaflet** for interactive maps
- **Axios** for API communication
- **Lucide React** for beautiful icons

## Getting Started

### Prerequisites

- Node.js 16+
- npm or yarn
- Backend API running on http://localhost:5000

### Installation

1. Install dependencies:
   ```bash
   npm install
   ```

2. Create a `.env` file:
   ```bash
   REACT_APP_API_URL=http://localhost:5000
   ```

3. Start the development server:
   ```bash
   npm start
   ```

4. Open [http://localhost:3000](http://localhost:3000) in your browser

### Building for Production

```bash
npm run build
```

This creates an optimized production build in the `build` folder.

## Project Structure

```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   ├── RegionSelector.tsx    # Region selection UI
│   │   ├── RouteMap.tsx          # Interactive Leaflet map
│   │   ├── DayDetails.tsx        # Day-by-day hiking details
│   │   └── LoadingSpinner.tsx    # Loading state component
│   ├── services/
│   │   └── api.ts                # API client
│   ├── types.ts                  # TypeScript interfaces
│   ├── App.tsx                   # Main application
│   └── index.css                 # Global styles with Tailwind
├── tailwind.config.js
└── package.json
```

## API Integration

The frontend communicates with the Flask backend API:

- `GET /api/regions` - Fetch available regions
- `POST /api/{region}/generate-interactive-route` - Start route generation
- `GET /api/{region}/route-status/:jobId` - Check generation status

## Customization

### Adding New Regions

1. Backend must support the new region in `/api/regions`
2. Add region icon in `RegionSelector.tsx`
3. Update terrain types in `DayDetails.tsx` if needed

### Styling

Modify `tailwind.config.js` to customize:
- Color schemes
- Spacing
- Breakpoints
- Typography

## Deployment

### Heroku

1. Add `heroku-buildpack-nodejs`
2. Set environment variables
3. Deploy the `frontend` directory

### Netlify / Vercel

1. Connect your repository
2. Set build command: `npm run build`
3. Set publish directory: `build`
4. Add environment variable: `REACT_APP_API_URL`

## License

MIT
