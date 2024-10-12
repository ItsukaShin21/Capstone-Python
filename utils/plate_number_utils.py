import requests
from config import API_URL

def check_plate_identity(plate_number):
    # Check detected text with the backend API
    db_check_response = requests.get(f"{API_URL}/check-text/{plate_number}")

    if db_check_response.status_code == 200:
        response_data = db_check_response.json()

        if "Identity" in response_data:
            identity = response_data["Identity"]
            print(identity)
        else:
            identity = "No record"
    else:
        identity = "No record"

    # Set the color based on the identity
    if identity == "Employee":
        color = (0, 255, 0)  # Green for Employee
    elif identity == "Visitor":
        color = (0, 165, 255)  # Orange for Visitor
    else:
        color = (0, 0, 255)  # Red for No record

    return color

def log_plate_number(plate_number):
    requests.post(f"{API_URL}/add-record-log/{plate_number}")