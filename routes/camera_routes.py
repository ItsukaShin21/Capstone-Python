from flask import Blueprint, jsonify
import requests
from config import API_URL

# Create a Blueprint for camera routes
camera_bp = Blueprint('camera', __name__)

@camera_bp.route('/cameras', methods=['GET'])
def get_cameras():
        # Query the cameras from the database
        db_response = requests.get(f"{API_URL}/fetch-cameras")

        cameras = db_response.json().get("cameraLists", [])

        return jsonify(cameras)