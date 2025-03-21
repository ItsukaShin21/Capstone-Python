from flask import Blueprint, Response, jsonify
import cv2
from models.camera import Camera
from utils.camera_utils import run_yolo_detection
from models.vehicle import Vehicle
from shared_data import registered_vehicles
import time

FETCH_INTERVAL = 2  # Interval to refresh vehicle list
last_fetch_time = time.time() - FETCH_INTERVAL  # Ensure immediate fetch on first run

# Create a Blueprint for video routes
video_bp = Blueprint('video', __name__)

def fetch_camera_by_id(camera_id):
    """Fetch camera details by ID from the database."""
    camera = Camera.query.get(camera_id)
    return {
        "id": camera.id,
        "camera_name": camera.camera_name,
        "rtsp_url": camera.rtsp_url,
        "location": camera.location,
        "camera_type": camera.camera_type
    } if camera else None

def fetch_vehicles():
    """Fetch the list of registered vehicles from the database."""
    global registered_vehicles
    try:
        vehicles = Vehicle.query.all()
        print(f"Fetched {len(vehicles)} vehicles from the database.")
        # Clear the existing list and populate it with new data
        registered_vehicles.clear()
        registered_vehicles.extend([
            {
                "plate_number": vehicle.plate_number,
                "username": vehicle.username,
                "identity": vehicle.identity,
                "status": vehicle.status
            }
            for vehicle in vehicles
        ])
        print("Vehicle list refreshed from the database.")
    except Exception as e:
        print(f"Error fetching vehicle data from database: {str(e)}")

@video_bp.route('/video_feed/<int:camera_id>', methods=['GET'])
def video_feed(camera_id):
    global last_fetch_time, registered_vehicles

    current_time = time.time()
    if current_time - last_fetch_time >= FETCH_INTERVAL:
        fetch_vehicles()
        last_fetch_time = current_time

    """Stream video feed with YOLO detection."""
    camera = fetch_camera_by_id(camera_id)  # Fetch the camera data once
    if not camera:
        return Response("Camera not found", status=404)

    # Capture the RTSP stream using OpenCV
    # cap = cv2.VideoCapture(f"C:\\Users\\LENOVO\\Documents\\python\\capstone-backend\\main\\video5(3-3).mp4")
    cap = cv2.VideoCapture(camera["rtsp_url"], cv2.CAP_FFMPEG)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)      
    cap.set(cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_ANY)

    def generate():
        frame_interval =  30 # 10
        frame_count = 0  # Track the frame count
        while True:
            ret, frame = cap.read()
            if not ret:
                cap.release()
                cap = cv2.VideoCapture(camera["rtsp_url"], cv2.CAP_FFMPEG)
                continue
            
            # Run detection every 10 frames
            if frame_count % frame_interval == 0:
                frame_with_detection = run_yolo_detection(frame, camera_id)
            else:
                frame_with_detection = frame  # Skip detection, just send the frame

            # Resize the frame to fit 640x400 without cropping
            frame_resized = cv2.resize(frame_with_detection, (640, 400))

            # Convert the frame to JPEG format
            _, jpeg = cv2.imencode('.jpg', frame_resized)

            # Yield the frame as byte data for streaming
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')
            
            frame_count += 1  # Increment the frame count

        cap.release()  # Ensure resources are released when done

    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')