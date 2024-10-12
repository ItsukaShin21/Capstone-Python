from flask import Blueprint, Response, jsonify
import cv2
import requests
from config import LARAVEL_API_URL
from utils.camera_utils import run_yolo_detection

# Create a Blueprint for video routes
video_bp = Blueprint('video', __name__)

@video_bp.route('/video_feed/<int:camera_id>')
def video_feed(camera_id):
    # Retrieve the camera from the Laravel API
    response = requests.get(LARAVEL_API_URL)
    if response.status_code != 200:
        return jsonify({'error': 'Could not fetch cameras from the Laravel API'}), 500
    
    cameras = response.json().get('cameraLists', [])
    camera = next((cam for cam in cameras if cam['id'] == camera_id), None)

    if not camera:
        return jsonify({'error': 'Camera not found'}), 404

    # Capture the RTSP stream
    cap = cv2.VideoCapture(camera['rtsp_url'])

    def generate():
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Resize the frame to fit 650x400 without cropping
            frame = cv2.resize(frame, (650, 400))

            # Run YOLO detection and OCR on the frame
            frame_with_detection = run_yolo_detection(frame)

            # Convert the frame to JPEG format
            _, jpeg = cv2.imencode('.jpg', frame_with_detection)

            # Yield the frame as byte data for streaming
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')

    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')