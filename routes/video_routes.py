from flask import Blueprint, Response, jsonify
import cv2
import requests
from config import API_URL
from utils.camera_utils import run_yolo_detection

# Create a Blueprint for video routes
video_bp = Blueprint('video', __name__)

def fetch_camera_by_id(camera_id):
    """Fetch camera details by ID."""
    try:
        response = requests.get(f"{API_URL}/fetch-cameras", timeout=5)
        cameras = response.json().get("cameraLists", [])
        return next((cam for cam in cameras if cam["id"] == camera_id), None)
    except requests.RequestException as e:
        print(f"Error fetching cameras: {e}")
        return None

@video_bp.route('/video_feed/<int:camera_id>', methods=['GET'])
def video_feed(camera_id):
    """Stream video feed with YOLO detection."""
    camera = fetch_camera_by_id(camera_id)  # Fetch the camera data once
    if not camera:
        return Response("Camera not found", status=404)

    # Capture the RTSP stream using OpenCV
    # cap = cv2.VideoCapture(f"C:\\Users\\LENOVO\\Documents\\python\\capstone-backend\\main\\sample.mp4")
    cap = cv2.VideoCapture(camera["rtsp_url"])

    def generate():
        frame_interval = 1  
        frame_count = 0  # Track the frame count
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Run detection every 10 frames
            if frame_count % frame_interval == 0:
                frame_with_detection = run_yolo_detection(frame, camera_id)
            else:
                frame_with_detection = frame  # Skip detection, just send the frame

            # Resize the frame to fit 640x400 without cropping
            frame_resized = cv2.resize(frame_with_detection, (320, 320))

            # Convert the frame to JPEG format
            _, jpeg = cv2.imencode('.jpg', frame_resized)

            # Yield the frame as byte data for streaming
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')
            
            frame_count += 1  # Increment the frame count

        cap.release()  # Ensure resources are released when done

    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')