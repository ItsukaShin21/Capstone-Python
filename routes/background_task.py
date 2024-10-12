from flask import Blueprint, Response, jsonify
import cv2
import requests
from config import LARAVEL_API_URL
from utils.camera_utils import run_yolo_detection
import threading
import time

# Create a Blueprint for video routes
background_task_bp = Blueprint('background_task', __name__)

def background_task(camera_id):
    # Retrieve the camera from the Laravel API
    response = requests.get(LARAVEL_API_URL)
    if response.status_code != 200:
        print('Could not fetch cameras from the Laravel API')
        return
    
    cameras = response.json().get('cameraLists', [])
    camera = next((cam for cam in cameras if cam['id'] == camera_id), None)

    if not camera:
        print('Camera not found')
        return

    # Capture the RTSP stream
    cap = cv2.VideoCapture(camera['rtsp_url'])

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Resize the frame to fit 650x400 without cropping
        frame = cv2.resize(frame, (650, 400))

        # Run YOLO detection and OCR on the frame
        frame_with_detection = run_yolo_detection(frame)

        # Here, you can log data, process frames, or send them to an API
        print(f"Processing frame from camera {camera_id}")

        # Add a sleep to avoid overloading the system
        time.sleep(1)  # Adjust the sleep time based on how often you want the task to run

