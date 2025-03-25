import cv2
from ultralytics import YOLO
import easyocr
from fast_plate_ocr import ONNXPlateRecognizer
import numpy as np
import time
from datetime import datetime
from pytz import timezone
from utils.plate_number_utils import log_plate_number, get_plate_identity
from utils.alarm_utils import send_alarm_notification, send_info_notification
import time
from shared_data import registered_vehicles
import re

# Load YOLO model
yolo_model = YOLO(r'C:\Users\LENOVO\Documents\python\capstone-backend\main\best.pt')
# yolo_model = YOLO('/home/ubuntu/capstone-backend/best.pt')


# Initialize EasyOCR reader
reader = easyocr.Reader(['en'], gpu=True)
# reader = ONNXPlateRecognizer("global-plates-mobile-vit-v2-model")
# reader = ONNXPlateRecognizer(model_path=r"C:\Users\LENOVO\Documents\python\capstone-backend\main\ocr_models\model.onnx",
#                              config_path=r"C:\Users\LENOVO\Documents\python\capstone-backend\main\ocr_models\config.yaml")

# Detection timing parameters
detection_times = {}  # To track detection times for bounding boxes
ALARM_THRESHOLD_SECONDS = 1  # 3 minutes
FETCH_INTERVAL = 10  # Interval to refresh vehicle list
last_fetch_time = time.time() - FETCH_INTERVAL  # Ensure immediate fetch on first run
current_time = time.time()

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

def is_valid_plate_format(plate_text):
    """Check if the detected text matches the Philippine plate format.
    Accepts both the new format (3 letters and 4 numbers) and the old format (3 letters and 3 numbers).
    """
    plate_text = plate_text.replace("_", "")
    return bool(re.match(r"^[A-Z]{3}\d{3}$", plate_text)) or bool(re.match(r"^[A-Z]{3}\d{4}$", plate_text))
    # return bool(re.match(r"^[A-Z0-9]{6,7}$", plate_text))

# def process_roi(roi):
#     """Process the ROI to enhance text detection."""
#     # Step 1: Scale up the image
#     roi_scaled = cv2.resize(roi, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

#     # Step 2: Reduce to 8 colors using k-means clustering
#     Z = roi_scaled.reshape((-1, 3))  # Reshape to 2D array of pixels
#     Z = np.float32(Z)
#     K = 8  # Number of colors
#     criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
#     _, labels, centers = cv2.kmeans(Z, K, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
#     centers = np.uint8(centers)
#     segmented_img = centers[labels.flatten()]
#     roi_kmeans = segmented_img.reshape(roi_scaled.shape)

#     # Step 3: Convert to grayscale and apply adaptive thresholding
#     roi_gray = cv2.cvtColor(roi_kmeans, cv2.COLOR_BGR2GRAY)
#     roi_thresh = cv2.adaptiveThreshold(
#         roi_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
#     )

#     # Step 4: Apply erosion to close gaps in letters
#     kernel = np.ones((3, 3), np.uint8)  # Kernel size can be adjusted
#     roi_eroded = cv2.erode(roi_thresh, kernel, iterations=1)

#     return roi_eroded

def run_yolo_detection(frame, camera_id):
    """Run YOLO detection and process results for license plate recognition."""
    global detection_times, last_fetch_time, registered_vehicles

    results = yolo_model.track(frame, persist=True, stream=True)
    updated_detection_times = {}

    for result in results:
        boxes = result.boxes

        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            current_box = (x1, y1, x2, y2)
            roi = frame[int(y1):int(y2), int(x1):int(x2)]

            roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            # roi_gray_float = roi_gray.astype(np.float32) / 255.0

            # Process ROI using the new steps
            # processed_roi = process_roi(roi)

            cv2.imwrite("roi.jpg", roi_gray)

            # Perform OCR
            ocr_results = reader.readtext(
                roi_gray,
                allowlist="ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890",
                blocklist="!@#$%&*()+-_|}{:;",
                link_threshold=0.0,
                contrast_ths=0.3,
                adjust_contrast=0.2,
                filter_ths=0.5
            )


            # detected_text = reader.run(roi_gray)
            # print(detected_text)
            for (bbox, text, prob) in ocr_results:
                if prob > 0.8:
                    detected_text = text
                    print(detected_text)
            if isinstance(detected_text, list) and detected_text:
                detected_text = detected_text[0]  # Extract first element
                detected_text = detected_text.replace("_", "").strip() 
            else:
                detected_text = ""  # Default to empty string if nothing is detected

            identity = get_plate_identity(detected_text, registered_vehicles)

            matched = False
            display_text = "Unregistered"

            for tracked_box, start_time in detection_times.items():
                if iou(tracked_box, current_box) > 0.0:  # IoU threshold
                    matched = True
                    elapsed_time = current_time - start_time

                    # Check identity and assign color
                    if detected_text:
                        identity = get_plate_identity(detected_text, registered_vehicles)
                        if identity == "Employee":
                            color = (0, 255, 0)  # Green
                            display_text = "Employee"
                            log_plate_number(detected_text, camera_id, registered_vehicles)
                            updated_detection_times[current_box] = current_time  # Reset timer
                        elif identity == "Visitor":
                            color = (255, 0, 0)  # Blue
                            display_text = "Visitor"
                            log_plate_number(detected_text, camera_id, registered_vehicles)
                            updated_detection_times[current_box] = current_time  # Reset timer
                        elif identity == "Dropoff":
                            color = (255, 0, 0)
                            display_text = "Drop-off"
                            log_plate_number(detected_text, camera_id, registered_vehicles)
                            updated_detection_times[current_box] = current_time
                        elif identity == "ILSparent":
                            color = (255, 0, 0)
                            display_text = "ILS Parent"
                            log_plate_number(detected_text, camera_id, registered_vehicles)
                            updated_detection_times[current_box] = current_time
                        else:
                            # Unrecognized, check alarm conditions
                            color = (0, 165, 255)  # Orange for unregistered
                            display_text = "Unregistered"
                            if is_valid_plate_format(detected_text):
                                log_plate_number(detected_text, camera_id, registered_vehicles)
                            if elapsed_time >= ALARM_THRESHOLD_SECONDS:
                                color = (0, 0, 255)  # Red for alarm
                            updated_detection_times[current_box] = start_time  # Keep original timer
                    else:
                        # Default color for unrecognized text
                        color = (0, 165, 255)
                        if is_valid_plate_format(detected_text):
                            log_plate_number(detected_text, camera_id, registered_vehicles)
                        if elapsed_time >= ALARM_THRESHOLD_SECONDS:
                            color = (0, 0, 255)  # Red for alarm
                        updated_detection_times[current_box] = start_time  # Keep original timer
                    break

            if not matched:
                # Add new box to tracking
                updated_detection_times[current_box] = current_time
                color = (0, 165, 255)  # Default blue for unregistered

                if detected_text:
                    identity = get_plate_identity(detected_text, registered_vehicles)
                    if identity == "Employee":
                        color = (0, 255, 0)  # Green
                        display_text = "Employee"
                        log_plate_number(detected_text, camera_id, registered_vehicles)
                    elif identity == "Visitor":
                        color = (255, 0, 0)  # Orange
                        display_text = "Visitor"
                        log_plate_number(detected_text, camera_id, registered_vehicles)
                    elif identity == "Dropoff":
                        color = (255, 0, 0)
                        display_text = "Drop-off"
                        log_plate_number(detected_text, camera_id, registered_vehicles)
                    elif identity == "ILSparent":
                        color = (255, 0, 0)
                        display_text = "ILS Parent"
                        log_plate_number(detected_text, camera_id, registered_vehicles)
                    elif identity == "Unregistered":
                        color = (0, 165, 255)
                        display_text = "Unregistered"
                        if is_valid_plate_format(detected_text):
                            log_plate_number(detected_text, camera_id, registered_vehicles)

            # Draw rectangle with the assigned color
            # text_size = cv2.getTextSize(display_text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
            # text_x = int(x1)
            # text_y = int(y1) - 10  # Position the text above the bounding box
            # box_coords = ((text_x, text_y - text_size[1] - 10), (text_x + text_size[0] + 10, text_y + 5))
            # cv2.rectangle(frame, box_coords[0], box_coords[1], color, cv2.FILLED)
            # cv2.putText(frame, display_text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
            # cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 10)

            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 10)

    detection_times = updated_detection_times  # Update tracking times
    return frame