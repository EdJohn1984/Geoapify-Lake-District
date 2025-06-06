from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from rq import Queue
from redis import Redis
from worker import route_queue
import json
from geoapify_planner import generate_hiking_route

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Route generation task
def generate_route():
    print("[LOG] Starting generate_route")
    try:
        # Load waypoints from file
        with open('filtered_waypoints.json', 'r') as f:
            waypoints = json.load(f)
            
        # Create a dictionary of waypoint names
        waypoint_dict = {wp['properties']['name']: wp for wp in waypoints}
        
        # Always generate a 3-day hiking route dynamically
        result = generate_hiking_route(waypoint_dict, num_days=3)
        print("[LOG] generate_hiking_route finished")
        if not result:
            print("[LOG] No valid route found")
            return {
                'status': 'error',
                'message': 'No valid route found'
            }
            
        # Format the response
        print("[LOG] Route generated successfully")
        return {
            'status': 'success',
            'route': {
                'waypoints': result['waypoints'],
                'legs': [
                    {
                        'from': result['waypoints'][i],
                        'to': result['waypoints'][i+1],
                        'distance': leg['properties']['distance'] / 1000,  # Convert to km
                        'duration': leg['properties']['time'] / 60,  # Convert to minutes
                        'geometry': leg['geometry'],
                        'surface_percentages': leg.get('surface_percentages', {})
                    }
                    for i, leg in enumerate(result['legs'])
                ]
            },
            'message': 'Route generated successfully'
        }
    except Exception as e:
        print(f"[LOG] Exception in generate_route: {e}")
        return {
            'status': 'error',
            'message': str(e)
        }

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

if __name__ == '__main__':
    app.run(debug=True) 