from flask import Flask, jsonify, request
from geoapify_planner import generate_hiking_route
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/api/generate-route', methods=['POST'])
def generate_route():
    try:
        data = request.get_json()
        num_days = data.get('num_days', 3)
        num_tries = data.get('num_tries', 200)
        
        # Get route data without map generation
        result = generate_hiking_route(num_days=num_days, num_tries=num_tries, generate_map=False)
        
        # Format the response
        response = {
            'days': result['days'],
            'coordinates': result['coordinates']  # This will be used by the client to generate the map
        }
        return jsonify(response)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

# This is needed for Vercel
if __name__ == '__main__':
    app.run(debug=True, port=5000) 