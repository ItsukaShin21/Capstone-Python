from flask import Blueprint, jsonify
from config import API_URL
import requests

alarm_bp = Blueprint('alarm', __name__)

alarm_triggered = False
location = ""

@alarm_bp.route("/send-alarm")
def send_alarm_route():
    global alarm_triggered
    global location
    if alarm_triggered:
        alarm_triggered = False  # Reset the alarm after notifying
        return jsonify({"message": "Alarm", "location" : location}), 200
    else:
        return jsonify({"message": "No Alarm"}), 200

def send_alarm_notification(camera_id):
    global alarm_triggered
    global location

    try:
        # Query the camera by camera_id
        db_response = requests.get(f"{API_URL}/check-location/{camera_id}")

        response_data = db_response.json()

        # Check if location is in the response
        if "location" in response_data:
            location = response_data["location"]
        else:
            print(f"No location data found for camera ID {camera_id}")
            location = "Unknown Location"

        alarm_triggered = True  # Trigger the alarm

    except Exception as e:
        # Handle any potential errors
        print(f"Error fetching camera location: {str(e)}")
        location = "Error occurred"