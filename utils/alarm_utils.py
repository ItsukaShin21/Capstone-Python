from flask import Blueprint, jsonify

alarm_bp = Blueprint('alarm', __name__)

alarm_triggered = False

@alarm_bp.route("/send-alarm")
def send_alarm_route():
    global alarm_triggered
    if alarm_triggered:
        alarm_triggered = False  # Reset the alarm after notifying
        return jsonify({"message": "Alarm"}), 200
    else:
        return jsonify({"message": "No Alarm"}), 200

def send_alarm_notification():
    global alarm_triggered
    alarm_triggered = True
    print("Alarm triggered!")