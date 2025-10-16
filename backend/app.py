"""
Unified Flask application for multi-region hiking trip organizer.
"""
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Fix macOS fork() issue
os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES'

from .config import DEBUG, CORS_ORIGINS
from .regions.registry import region_registry
from .services.route_planner import RoutePlanner
from .tasks.route_tasks import route_queue, generate_route_task

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, origins=CORS_ORIGINS)

# Initialize services
route_planner = RoutePlanner()


@app.route('/api/regions', methods=['GET'])
def get_regions():
    """Get all available regions."""
    try:
        regions = region_registry.to_api_format()
        return jsonify({'regions': regions})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/regions/<region_id>', methods=['GET'])
def get_region_info(region_id):
    """Get information about a specific region."""
    try:
        region = region_registry.get_region(region_id)
        if not region:
            return jsonify({'error': 'Region not found'}), 404
        
        # Load waypoints to get stats
        waypoints = region_registry.load_waypoints(region_id)
        scenic_points = route_planner._get_scenic_points(region_id)
        
        return jsonify({
            'region': region_id,
            'name': region.name,
            'description': region.description,
            'waypoints_count': len(waypoints),
            'scenic_points_count': len(scenic_points),
            'features': [
                f'{region.route_params.default_days}-day hiking routes',
                'Scenic midpoint integration',
                'Distance range: {}-{}km per day'.format(
                    region.route_params.min_distance_km,
                    region.route_params.max_distance_km
                ),
                'GeoJSON export for web maps'
            ],
            'sample_waypoints': [wp['properties']['name'] for wp in waypoints[:10]]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/regions/<region_id>/routes', methods=['POST'])
def generate_route(region_id):
    """Generate a hiking route for a region."""
    try:
        # Validate region exists
        if not region_registry.region_exists(region_id):
            return jsonify({'error': 'Region not found'}), 404
        
        # Get request parameters
        data = request.get_json() or {}
        num_days = data.get('num_days')
        max_tries = data.get('max_tries')
        good_enough_threshold = data.get('good_enough_threshold')
        # Enqueue background job to avoid request timeouts
        job = route_queue.enqueue(
            generate_route_task,
            region_id,
            num_days=num_days,
            max_tries=max_tries,
            good_enough_threshold=good_enough_threshold,
            job_timeout=3600  # seconds
        )
        
        return jsonify({
            'status': 'queued',
            'job_id': job.get_id(),
            'region': region_id
        }), 202
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/regions/<region_id>/routes/<job_id>', methods=['GET'])
def get_route_status(region_id, job_id):
    """Get the status of a route generation job."""
    try:
        # Validate region exists
        if not region_registry.region_exists(region_id):
            return jsonify({'error': 'Region not found'}), 404
        
        job = route_queue.fetch_job(job_id)
        
        if not job:
            return jsonify({'status': 'not_found'}), 404
        
        if job.is_finished:
            return jsonify({
                'status': 'completed',
                'result': job.result,
                'region': region_id
            })
        elif job.is_failed:
            return jsonify({
                'status': 'failed',
                'error': str(job.exc_info),
                'region': region_id
            })
        else:
            return jsonify({
                'status': 'in_progress',
                'region': region_id
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'regions_loaded': len(region_registry.list_regions())
    })


if __name__ == '__main__':
    app.run(debug=DEBUG)