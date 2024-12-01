import cv2
from ultralytics import YOLO
import easyocr
import numpy as np
import time
import requests
from datetime import datetime
from pytz import timezone
from config import API_URL
from utils.plate_number_utils import log_plate_number, get_plate_identity
from utils.alarm_utils import send_alarm_notification

# Load YOLO model
yolo_model = YOLO(r'/home/ubuntu/flask-backend/model.pt').to('cuda')

# Initialize EasyOCR reader
reader = easyocr.Reader(['en'], gpu=True)

# Detection timing parameters
detection_times = {}  # To track detection times for bounding boxes
ALARM_THRESHOLD_SECONDS = 180  # 3 minutes
FETCH_INTERVAL = 20  # Interval to refresh vehicle list
last_fetch_time = time.time() - FETCH_INTERVAL  # Ensure immediate fetch on first run

# Cache registered vehicle list
registered_vehicles = []
last_vehicle_fetch_time = 0
FETCH_INTERVAL = 20  # Refresh interval for vehicle list (seconds)

def fetch_vehicles():
    """Fetch the list of registered vehicles from the database."""
    global registered_vehicles
    try:
        db_response = requests.get(f"{API_URL}/fetch-vehicles", timeout=5)
        registered_vehicles = db_response.json().get("vehicleList", [])
        print("Vehicle list refreshed")
    except requests.RequestException as e:
        print(f"Error fetching vehicle data: {e}")

fetch_vehicles()  # Initial fetch

def is_philippine_time(target_hour):
    """Check if the current time in Philippine timezone matches the target hour."""
    philippine_tz = timezone('Asia/Manila')
    current_time = datetime.now(philippine_tz)
    return current_time.hour > target_hour

def iou(box1, box2):
    """Calculate Intersection over Union (IoU) for two bounding boxes."""
    x1, y1, x2, y2 = box1
    x3, y3, x4, y4 = box2

    # Calculate intersection
    inter_x1 = max(x1, x3)
    inter_y1 = max(y1, y3)
    inter_x2 = min(x2, x4)
    inter_y2 = min(y2, y4)
    inter_area = max(0, inter_x2 - inter_x1) * max(0, inter_y2 - inter_y1)

    # Calculate union
    box1_area = (x2 - x1) * (y2 - y1)
    box2_area = (x4 - x3) * (y4 - y3)
    union_area = box1_area + box2_area - inter_area

    return inter_area / union_area if union_area > 0 else 0

def run_yolo_detection(frame, camera_id):
    """Run YOLO detection and process results for license plate recognition."""
    global detection_times, last_fetch_time

    current_time = time.time()
    if current_time - last_fetch_time >= FETCH_INTERVAL:
        fetch_vehicles()
        last_fetch_time = current_time

    results = yolo_model.track(frame, persist=True)
    updated_detection_times = {}

    for result in results:
        boxes = result.boxes

        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            roi = frame[int(y1):int(y2), int(x1):int(x2)]
            roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            cv2.imwrite("roi.jpg", roi_gray)
            # Perform OCR
            ocr_results = reader.readtext(
                roi_gray,
                allowlist="ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890",
                blocklist="!@#$%&*()+-_|}{:;",
                link_threshold=0.0,
                contrast_ths=0.3,
                adjust_contrast=0.7,
                filter_ths=0.020
            )

            detected_text = ''
            for (bbox, text, prob) in ocr_results:
                if prob > 0:
                    detected_text = text
                    print(detected_text)

            current_box = (x1, y1, x2, y2)
            matched = False

            for tracked_box, start_time in detection_times.items():
                if iou(tracked_box, current_box) > 0.5:  # IoU threshold
                    matched = True
                    updated_detection_times[current_box] = start_time
                    elapsed_time = current_time - start_time

                    if elapsed_time >= ALARM_THRESHOLD_SECONDS:
                        color = (255, 0, 0)  # Blue for alarm
                        send_alarm_notification(camera_id)
                    else:
                        color = (0, 0, 255)  # Red for unregistered
                    break

            if not matched:
                updated_detection_times[current_box] = current_time
                color = (0, 0, 255)  # Default red for unregistered

            if detected_text:
                identity = get_plate_identity(detected_text, registered_vehicles)
                if identity == "Employee":
                    color = (0, 255, 0)  # Green for employee
                    log_plate_number(detected_text, camera_id)
                elif identity == "Visitor":
                    color = (0, 165, 255)  # Orange for visitor
                    log_plate_number(detected_text, camera_id)
                    if is_philippine_time(15):
                        send_alarm_notification(camera_id)

            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 10)

    detection_times = updated_detection_times  # Update tracking
    return frame