from flask import Blueprint, Response, jsonify
import cv2
from sqlalchemy.orm import sessionmaker
from models.camera import Camera
from config import engine
from utils.camera_utils import run_yolo_detection

# Create a Blueprint for video routes
video_bp = Blueprint('video', __name__)

# Create a session
Session = sessionmaker(bind=engine)
session = Session()

@video_bp.route('/video_feed/<int:camera_id>', methods=['GET'])
def video_feed(camera_id):
    try:
        # Query the camera from the database
        camera = session.query(Camera).filter_by(id=camera_id).first()

        if not camera:
            return jsonify({'error': 'Camera not found'}), 404

        # Capture the RTSP stream
        cap = cv2.VideoCapture(camera.rtsp_url)

        def generate():
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # Resize the frame to fit 650x400 without cropping
                frame = cv2.resize(frame, (650, 400))

                # Run YOLO detection and OCR on the frame
                frame_with_detection = run_yolo_detection(frame, camera_id)

                # Convert the frame to JPEG format
                _, jpeg = cv2.imencode('.jpg', frame_with_detection)

                # Yield the frame as byte data for streaming
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')

        return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

    except Exception as e:
        # In case of an error, return a 500 status with an error message
        return jsonify({'error': str(e)}), 500