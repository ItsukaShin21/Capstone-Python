import cv2
from ultralytics import YOLO
import easyocr
import numpy as np
import time
import requests
from requests.exceptions import ConnectTimeout
from config import API_URL
from utils.plate_number_utils import log_plate_number, get_plate_identity
from utils.alarm_utils import send_alarm_notification

# Load YOLO model
yolo_model = YOLO(r'C:\Users\LENOVO\Documents\python\capstone-backend\main\model.pt').to('cuda')

# Initialize EasyOCR reader
reader = easyocr.Reader(['en'], gpu=True)

no_record_start_time = None
ALARM_THRESHOLD_SECONDS = 5  # Set the threshold to 5 seconds for the alarm
FETCH_INTERVAL = 10  # Interval in seconds to refresh vehicle list
last_fetch_time = time.time() - FETCH_INTERVAL  # Initialize to fetch immediately on first run

# Initialize vehicle list
registered_vehicles = []

def fetch_vehicles():
    global registered_vehicles
    db_response = requests.get(f"{API_URL}/fetch-vehicles", timeout=5)
    registered_vehicles = db_response.json().get("vehicleList", [])
    print("Data refreshed")

fetch_vehicles()  # Initial fetch

def run_yolo_detection(frame, camera_id):
    global no_record_start_time, last_fetch_time

    # Update the vehicle list every 10 seconds
    current_time = time.time()
    if current_time - last_fetch_time >= FETCH_INTERVAL:
        fetch_vehicles()
        last_fetch_time = current_time

    # Run YOLO detection on the frame
    results = yolo_model.track(frame, persist=True)

    for result in results:
        boxes = result.boxes  # YOLO detected bounding boxes

        for box in boxes:
            # Extract bounding box coordinates
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            # Crop the detected area (ROI)
            roi = frame[int(y1):int(y2), int(x1):int(x2)]
            # Convert the ROI to grayscale
            roi_upscaled = cv2.resize(roi, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
            roi_bright = cv2.convertScaleAbs(roi_upscaled, alpha=1.5, beta=20)
            sharpening_kernel = np.array([[0, -1, 0],
                              [-1, 5, -1],
                              [0, -1, 0]])
            roi_sharp = cv2.filter2D(roi_bright, -1, sharpening_kernel)
            roi_gray = cv2.cvtColor(roi_sharp, cv2.COLOR_BGR2GRAY)
            roi_thresh = cv2.adaptiveThreshold(roi_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            cv2.imwrite("roi.jpg", roi_thresh)
            # Perform OCR on the processed ROI
            ocr_results = reader.readtext(roi_thresh, allowlist="ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890", blocklist="!@#$%&*()+-_|}{:;")
            # allowlist="ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890", blocklist="!@#$%&*()+-_|}{:;"

            detected_text = ''
            for (bbox, text, prob) in ocr_results:
                if prob > 0:  # Filter by confidence
                    detected_text = text
                    print(detected_text)

            if detected_text:
                identity = get_plate_identity(detected_text, registered_vehicles)

                if identity == "Employee":
                    color = (0, 255, 0)
                    log_plate_number(detected_text, camera_id)
                else:
                    color = (0, 0, 255)
                
                if identity == "Unregistered":
                    # If "No record" is detected and no timer started, start the timer
                    if no_record_start_time is None:
                        no_record_start_time = time.time()
                    else:
                        # Check if the detection has lasted for more than 1 second
                        elapsed_time = time.time() - no_record_start_time
                        if elapsed_time >= ALARM_THRESHOLD_SECONDS:
                            send_alarm_notification(camera_id)
                            color = (255, 0, 0)
                else:
                    # Reset the timer if the identity is not "No record"
                    no_record_start_time = None
                
                if identity == "Visitor":
                    color = (0, 165, 255)
                    log_plate_number(detected_text, camera_id)

                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)

    return frame