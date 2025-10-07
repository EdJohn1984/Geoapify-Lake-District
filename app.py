from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from rq import Queue
from redis import Redis
from worker import route_queue
import json
from route_tasks import (
    generate_route, 
    generate_interactive_route, 
    generate_cornwall_route, 
    generate_cornwall_interactive_route
)

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Route generation functions are now imported from route_tasks.py

@app.route('/api/generate-route', methods=['POST'])
def create_route():
    # No need to parse or use request data
    job = route_queue.enqueue(
        generate_route,
        job_timeout='1h'  # Adjust timeout as needed
    )

    return jsonify({
        'job_id': job.id,
        'status': 'queued'
    })

@app.route('/api/generate-interactive-route', methods=['POST'])
def create_interactive_route():
    """Generate route data for interactive web maps (GeoJSON format)."""
    job = route_queue.enqueue(
        generate_interactive_route,
        job_timeout='1h'
    )
    
    return jsonify({
        'job_id': job.id,
        'status': 'queued',
        'format': 'geojson'
    })

# Cornwall API endpoints
@app.route('/api/cornwall/generate-route', methods=['POST'])
def create_cornwall_route():
    """Generate a Cornwall hiking route."""
    job = route_queue.enqueue(
        generate_cornwall_route,
        job_timeout='1h'
    )

    return jsonify({
        'job_id': job.id,
        'status': 'queued',
        'region': 'cornwall'
    })

@app.route('/api/cornwall/generate-interactive-route', methods=['POST'])
def create_cornwall_interactive_route():
    """Generate Cornwall route data for interactive web maps (GeoJSON format)."""
    job = route_queue.enqueue(
        generate_cornwall_interactive_route,
        job_timeout='1h'
    )
    
    return jsonify({
        'job_id': job.id,
        'status': 'queued',
        'format': 'geojson',
        'region': 'cornwall'
    })

@app.route('/api/cornwall/route-status/<job_id>', methods=['GET'])
def get_cornwall_route_status(job_id):
    """Get the status of a Cornwall route generation job."""
    job = route_queue.fetch_job(job_id)
    
    if not job:
        return jsonify({'status': 'not_found'}), 404
    
    if job.is_finished:
        return jsonify({
            'status': 'completed',
            'result': job.result,
            'region': 'cornwall'
        })
    elif job.is_failed:
        return jsonify({
            'status': 'failed',
            'error': str(job.exc_info),
            'region': 'cornwall'
        })
    else:
        return jsonify({
            'status': 'in_progress',
            'region': 'cornwall'
        })

@app.route('/api/route-status/<job_id>', methods=['GET'])
def get_route_status(job_id):
    job = route_queue.fetch_job(job_id)
    
    if not job:
        return jsonify({'status': 'not_found'}), 404
    
    if job.is_finished:
        return jsonify({
            'status': 'completed',
            'result': job.result
        })
    elif job.is_failed:
        return jsonify({
            'status': 'failed',
            'error': str(job.exc_info)
        })
    else:
        return jsonify({
            'status': 'in_progress'
        })

# Region information endpoints
@app.route('/api/regions', methods=['GET'])
def get_regions():
    """Get available regions for route planning."""
    return jsonify({
        'regions': [
            {
                'id': 'lake_district',
                'name': 'Lake District',
                'description': 'Mountain hiking routes in the Lake District National Park',
                'endpoints': {
                    'generate_route': '/api/generate-route',
                    'generate_interactive_route': '/api/generate-interactive-route',
                    'route_status': '/api/route-status'
                }
            },
            {
                'id': 'cornwall',
                'name': 'Cornwall',
                'description': 'Coastal and inland hiking routes in Cornwall',
                'endpoints': {
                    'generate_route': '/api/cornwall/generate-route',
                    'generate_interactive_route': '/api/cornwall/generate-interactive-route',
                    'route_status': '/api/cornwall/route-status'
                }
            }
        ]
    })

@app.route('/api/cornwall/info', methods=['GET'])
def get_cornwall_info():
    """Get information about Cornwall route planning."""
    try:
        # Load Cornwall waypoints to get stats
        with open('cornwall_waypoints.json', 'r') as f:
            waypoints = json.load(f)
        
        # Load scenic points
        from cornwall_planner import get_cornwall_scenic_points
        scenic_points = get_cornwall_scenic_points()
        
        return jsonify({
            'region': 'cornwall',
            'waypoints_count': len(waypoints),
            'scenic_points_count': len(scenic_points),
            'description': 'Coastal and inland hiking routes in Cornwall with scenic highlights',
            'features': [
                '3-day hiking routes',
                'Scenic midpoint integration',
                'Coastal and inland waypoints',
                'Distance range: 8-18km per day',
                'GeoJSON export for web maps'
            ],
            'sample_waypoints': [wp['properties']['name'] for wp in waypoints[:10]]
        })
    except Exception as e:
        return jsonify({
            'region': 'cornwall',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True) 