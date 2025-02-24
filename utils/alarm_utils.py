from flask import Blueprint, jsonify
from models.camera import Camera

alarm_bp = Blueprint('alarm', __name__)
send_info_bp = Blueprint('send_info', __name__)

alarm_triggered = False
location = ""
send_info_trigger = False
plate_number = ""
identity = ""
username = ""
email = ""
time_in = ""
time_out = ""
error = ""

@send_info_bp.route("/send-info")
def send_info_route():
    global send_info_trigger, plate_number, username, email, identity, time_in, time_out, error

    if send_info_trigger:
        if error and not any([plate_number, username, email, identity, time_in, time_out]):
            # If there's an error and the other fields are empty or None
            send_info_trigger = False
            return jsonify({"message": "error", "error": error}), 200
        elif plate_number and not any([ identity, time_out, error]):
            send_info_trigger = False
            return jsonify({"message":"New Info",
                            "plate_number": plate_number, 
                            "identity": identity, 
                            "time_in": time_in, 
                            "time_out": time_out
            }), 200
        else:
            send_info_trigger = False
            return jsonify({
                "message": "Info", 
                "plate_number": plate_number,
                "username": username,
                "email": email, 
                "identity": identity, 
                "time_in": time_in, 
                "time_out": time_out
            })

    return jsonify({"message": "No Info"}), 200

def send_info_notification(plate_number_param, username_param, email_param, identity_param, time_in_param, time_out_param, error_param):
    global send_info_trigger, plate_number, username, email, identity, time_in, time_out, error

    try:
        plate_number = plate_number_param
        username = username_param
        email = email_param
        identity = identity_param
        time_in = time_in_param
        time_out = time_out_param
        error = error_param
        
        send_info_trigger = True
    except Exception as e:
        print("Something is wrong:", e)

@alarm_bp.route("/send-alarm")
def send_alarm_route():
    global alarm_triggered
    global location
    if alarm_triggered:
        alarm_triggered = False  # Reset the alarm after notifying
        print("sended")
        return jsonify({"message" : "Alarm", "location" : location})
    else:
        return jsonify({"message": "No Alarm"}), 200

def send_alarm_notification(camera_id):
    global alarm_triggered
    global location

    try:
        # Query the camera by camera_id directly from the database
        camera = Camera.query.get(camera_id)

        if camera:
            location = camera.location
        else:
            print(f"No camera found for ID {camera_id}")
            location = "Unknown Location"

        alarm_triggered = True  # Trigger the alarm

    except Exception as e:
        print(f"Error fetching camera location from database: {str(e)}")
        location = "Database Error"