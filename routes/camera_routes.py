from flask import Blueprint, jsonify
from sqlalchemy.orm import sessionmaker
from models.camera import Camera
from config import engine

# Create a Blueprint for camera routes
camera_bp = Blueprint('camera', __name__)

# Create a session factory
Session = sessionmaker(bind=engine)

@camera_bp.route('/cameras', methods=['GET'])
def get_cameras():
    session = Session()  # Create a new session for each request
    try:
        # Query the cameras from the database
        cameras = session.query(Camera).all()

        # Convert the camera objects to a list of dictionaries
        cameraList = [
            {
                'id': camera.id,
                'camera_name': camera.camera_name,
                'rtsp_url': camera.rtsp_url,
                'location': camera.location,
                'camera_type': camera.camera_type,
                'created_at': camera.created_at,
                'updated_at': camera.updated_at
            }
            for camera in cameras
        ]

        return jsonify(cameraList), 200
    
    except Exception as e:
        # In case of an error, return a 500 status with an error message
        return jsonify({'error': str(e)}), 500

    finally:
        session.close()  # Ensure the session is closed after the request