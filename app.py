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
        
        result = generate_hiking_route(num_days=num_days, num_tries=num_tries)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000) 