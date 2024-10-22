import cv2
import requests
from ultralytics import YOLO
import easyocr
import numpy as np
import time
from config import API_URL
from utils.plate_number_utils import check_plate_identity, log_plate_number
from utils.alarm_utils import send_alarm_notification

# Load YOLO model
yolo_model = YOLO(r'C:\Users\LENOVO\Documents\python\capstone-backend\main\model.pt').to('cuda')

# Initialize EasyOCR reader
reader = easyocr.Reader(['en'], gpu=True)

# Initialize detection timing variables
no_record_start_time = None
ALARM_THRESHOLD_SECONDS = 1  # Set the threshold to 1 second for the alarm

def run_yolo_detection(frame, camera_id):
    global no_record_start_time

    # Run YOLO detection on the frame
    results = yolo_model(frame)

    for result in results:
        boxes = result.boxes  # YOLO detected bounding boxes

        for box in boxes:
            # Extract bounding box coordinates
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            # Crop the detected area (ROI)
            roi = frame[int(y1):int(y2), int(x1):int(x2)]
            # Convert the ROI to grayscale
            roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            # Apply Gaussian blur to reduce noise
            roi_denoised = cv2.GaussianBlur(roi_gray, (5, 5), 0)
            # Apply adaptive thresholding
            roi_thresh = cv2.adaptiveThreshold(roi_denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            # Apply sharpening using a kernel
            sharpening_kernel = np.array([[-1, -1, -1],
                                          [-1, 9, -1],
                                          [-1, -1, -1]])
            roi_sharp = cv2.filter2D(roi_thresh, -1, sharpening_kernel)
            # Adjust brightness
            roi_bright = cv2.convertScaleAbs(roi_sharp, alpha=1.2, beta=30)
            # Perform OCR on the processed ROI
            ocr_results = reader.readtext(roi_bright)

            detected_text = ''
            for (bbox, text, prob) in ocr_results:
                if prob > 0.5:  # Filter by confidence
                    detected_text = text
                    print(detected_text)
                    log_plate_number(detected_text, camera_id)

            if detected_text:
                color, identity = check_plate_identity(detected_text)

                # Check if the identity is "No record"
                if identity == "No record":
                    # If "No record" is detected and no timer started, start the timer
                    if no_record_start_time is None:
                        no_record_start_time = time.time()
                    else:
                        # Check if the detection has lasted for more than 1 second
                        elapsed_time = time.time() - no_record_start_time
                        if elapsed_time >= ALARM_THRESHOLD_SECONDS:
                            send_alarm_notification()
                            color = (0, 0, 255)
                else:
                    # Reset the timer if the identity is not "No record"
                    no_record_start_time = None

                # Draw bounding box and display detected text on the frame
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)

    return frame