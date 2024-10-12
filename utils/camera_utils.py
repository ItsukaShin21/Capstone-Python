import cv2
import requests
from ultralytics import YOLO
import easyocr
import numpy as np
from config import API_URL
from utils.plate_number_utils import check_plate_identity, log_plate_number

# Load YOLO model
yolo_model = YOLO(r'C:\Users\LENOVO\Documents\python\capstone-backend\main\model.pt').to('cuda');

# Initialize EasyOCR reader
reader = easyocr.Reader(['en'], gpu=True)

def run_yolo_detection(frame):
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
                    log_plate_number(detected_text)


            if detected_text:
                color = check_plate_identity(detected_text)

                # Draw bounding box and display detected text on the frame
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)

    return frame