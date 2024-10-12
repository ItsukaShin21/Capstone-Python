from flask import Blueprint, jsonify
import requests
from config import LARAVEL_API_URL

# Create a Blueprint for camera routes
camera_bp = Blueprint('camera', __name__)

@camera_bp.route('/cameras', methods=['GET'])
def get_cameras():
    response = requests.get(LARAVEL_API_URL)
    if response.status_code != 200:
        return jsonify({'error': 'Could not fetch cameras from the Laravel API'}), 500
    
    cameras = response.json().get('cameraLists', [])
    return jsonify(cameras)