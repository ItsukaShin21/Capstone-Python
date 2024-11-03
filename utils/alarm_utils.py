from flask import Blueprint, jsonify
from sqlalchemy.orm import sessionmaker
from models.camera import Camera
from config import engine

alarm_bp = Blueprint('alarm', __name__)

alarm_triggered = False
location = ""

Session = sessionmaker(bind=engine)

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

    session = Session()

    try:
        # Query the camera by camera_id
        camera = session.query(Camera).filter_by(id=camera_id).first()

        if camera:
            # Set the global location variable to the camera's location
            location = camera.location
        else:
            print(f"No camera found with ID {camera_id}")
            location = "Unknown Location"

        alarm_triggered = True  # Trigger the alarm

    except Exception as e:
        # Handle any potential errors
        print(f"Error fetching camera location: {str(e)}")
        location = "Error occurred"

    finally:
        # Always close the session
        session.close()