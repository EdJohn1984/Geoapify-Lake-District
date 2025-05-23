# Hiking Trip Organizer

A web application for organizing and managing hiking trips, built with Flask and React.

## Features

- User authentication and authorization
- Trip creation and management
- Trail information and weather integration
- Equipment checklist
- Trip sharing and collaboration
- Responsive design for mobile and desktop

## Tech Stack

### Backend
- Flask (Python web framework)
- SQLAlchemy (ORM)
- Flask-Login (Authentication)
- Flask-Mail (Email notifications)
- Flask-Migrate (Database migrations)
- Flask-CORS (Cross-origin resource sharing)
- Gunicorn (WSGI HTTP Server)

### Frontend
- React
- TypeScript
- Tailwind CSS
- React Router
- Axios

## Setup Instructions

### Prerequisites
- Python 3.11+
- Node.js 18+
- npm or yarn
- PostgreSQL (for production)

### Backend Setup
1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. Initialize the database:
   ```bash
   flask db upgrade
   ```

5. Run the development server:
   ```bash
   flask run
   ```

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

## Deployment

### Backend Deployment
1. Ensure all environment variables are set in your deployment platform
2. The application uses Gunicorn as the WSGI server
3. Database migrations will run automatically on deployment

### Frontend Deployment
1. Build the frontend:
   ```bash
   cd frontend
   npm run build
   ```
2. Deploy the built files to your hosting service

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 