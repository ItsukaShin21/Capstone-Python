from flask import Blueprint, request, jsonify
from models.camera import Camera
from extensions import db

camera_controller = Blueprint("camera_controller", __name__)

# Register Camera
@camera_controller.route('/add-camera', methods=['POST'])
def register_camera():
    data = request.get_json()

    try:
        # Validate input data
        required_fields = ["camera_name", "rtsp_url", "location", "camera_type"]
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"message": f"{field} is required"})

        # Check for uniqueness
        if Camera.query.filter_by(camera_name=data["camera_name"]).first():
            return jsonify({"message": "Camera name already exists"})

        if Camera.query.filter_by(rtsp_url=data["rtsp_url"]).first():
            return jsonify({"message": "RTSP URL already exists"})

        # Create new Camera
        camera = Camera(
            camera_name=data["camera_name"],
            rtsp_url=data["rtsp_url"],
            location=data["location"],
            camera_type=data["camera_type"]
        )

        db.session.add(camera)
        db.session.commit()

        return jsonify({"message": "success"})

    except Exception as e:
        return jsonify({"message": str(e)})

# Fetching all Cameras    
@camera_controller.route('/fetch-cameras', methods=['GET'])
def display_cameras():
    try:
        cameras = Camera.query.all()
        camera_list = [
            {
                "id": camera.id,
                "camera_name": camera.camera_name,
                "rtsp_url": camera.rtsp_url,
                "location": camera.location,
                "camera_type": camera.camera_type
            } for camera in cameras
        ]
        return jsonify({"cameraLists": camera_list})

    except Exception as e:
        return jsonify({"message": str(e)})

# Fetching a specific Camera    
@camera_controller.route('/fetch-camera/<int:id>', methods=['GET'])
def display_camera(id):
    try:
        camera = Camera.query.get(id)
        if not camera:
            return jsonify({"message": "Camera not found"})

        camera_details = {
            "id": camera.id,
            "camera_name": camera.camera_name,
            "rtsp_url": camera.rtsp_url,
            "location": camera.location,
            "camera_type": camera.camera_type
        }

        return jsonify({"cameraDetails": camera_details})

    except Exception as e:
        return jsonify({"message": str(e)})

# Update Camera Details
@camera_controller.route('/update-camera', methods=['POST'])
def update_camera():
    data = request.get_json()

    # Check for uniqueness
    if Camera.query.filter_by(camera_name=data["camera_name"]).first():
        return jsonify({"message": "Camera name already exists"})
    if Camera.query.filter_by(rtsp_url=data["rtsp_url"]).first():
        return jsonify({"message": "RTSP URL already exists"})

    try:
        # Validate input data
        required_fields = ["id", "camera_name", "rtsp_url", "location", "camera_type"]
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"message": f"{field} is required"})

        camera = Camera.query.get(data["id"])
        if not camera:
            return jsonify({"message": "Camera not found"})

        # Update camera details
        camera.camera_name = data["camera_name"]
        camera.rtsp_url = data["rtsp_url"]
        camera.location = data["location"]
        camera.camera_type = data["camera_type"]

        db.session.commit()

        return jsonify({"message": "success"})

    except Exception as e:
        return jsonify({"message": str(e)})


@camera_controller.route('/check-location/<int:camera_id>', methods=['GET'])
def check_camera_location(camera_id):
    try:
        camera = Camera.query.get(camera_id)
        if not camera:
            return jsonify({"location": "No Location"})

        return jsonify({"location": camera.location})

    except Exception as e:
        return jsonify({"message": str(e)})

# Delete Camera
@camera_controller.route('/delete-camera', methods=['POST'])
def delete_camera():
    data = request.get_json()

    try:
        if "id" not in data or not data["id"]:
            return jsonify({"message": "Camera ID is required"})

        camera = Camera.query.get(data["id"])
        if not camera:
            return jsonify({"message": "Camera not found"})

        db.session.delete(camera)
        db.session.commit()

        return jsonify({"message": "success"})

    except Exception as e:
        return jsonify({"message": str(e)})