from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from rq import Queue
from redis import Redis
from worker import route_queue
import json

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Route generation task
def generate_route(start_point, end_point, waypoints):
    # Dummy implementation for testing
    return {
        'route': [start_point] + waypoints + [end_point],
        'distance_km': 42,
        'status': 'success',
        'message': 'This is a dummy route for testing.'
    }

@app.route('/api/generate-route', methods=['POST'])
def create_route():
    data = request.json
    start_point = data.get('start_point')
    end_point = data.get('end_point')
    waypoints = data.get('waypoints', [])

    # Queue the route generation task
    job = route_queue.enqueue(
        generate_route,
        args=(start_point, end_point, waypoints),
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