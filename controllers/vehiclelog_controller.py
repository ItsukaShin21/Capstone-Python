from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from models.vehicle_log import VehicleLog
from models.vehicle import Vehicle
from models.camera import Camera
from models.archive_log import ArchiveLog
from extensions import db
from sqlalchemy import func, and_
from Levenshtein import distance as levenshtein_distance
from pytz import timezone
from utils.alarm_utils import send_info_notification

manila_timezone = timezone('Asia/Manila')

vehiclelog_controller = Blueprint("vehiclelog_controller", __name__)

def format_datetime_to_manila(dt):
    if dt:
        return dt.astimezone(manila_timezone).strftime('%Y-%m-%d %H:%M:%S %z')
    return None

@vehiclelog_controller.route('/fetch-vehicle-logs', methods=['GET'])
def display_vehicle_logs():
    # Retrieve vehicle logs with associated vehicle details
    vehicle_logs = db.session.query(
        VehicleLog.log_id,
        VehicleLog.plate_number,
        VehicleLog.username,
        VehicleLog.identity,
        VehicleLog.time_in,
        VehicleLog.time_out,
    ).all()

    # Convert results into a JSON-compatible format
    return jsonify({
        "vehicleLogsList": [
            {
                "log_id": log.log_id,
                "plate_number": log.plate_number,
                "time_in": format_datetime_to_manila(log.time_in),
                "time_out": format_datetime_to_manila(log.time_out),
                "username": log.username,
                "identity": log.identity,
            } for log in vehicle_logs
        ]
    })

@vehiclelog_controller.route('/fetch-archived-logs', methods=['GET'])
def display_archived_logs():
    archive_logs = db.session.query(
        ArchiveLog.log_id,
        ArchiveLog.plate_number,
        ArchiveLog.time_in,
        ArchiveLog.time_out,
        ArchiveLog.username,
        ArchiveLog.identity,
    ).all()

    return jsonify({
        "archiveLogsList": [
            {
                "log_id" : archive.log_id,
                "username" : archive.username,
                "plate_number" : archive.plate_number,
                "identity" : archive.identity,
                "time_in" : format_datetime_to_manila(archive.time_in),
                "time_out" : format_datetime_to_manila(archive.time_out),
            } for archive in archive_logs
    ]})

@vehiclelog_controller.route('/add-record-log', methods=['POST'])
def add_record_log():
    data = request.json
    plate_number = data.get('plate_number')
    camera_id = data.get('camera_id')
    registered_vehicles = Vehicle.query.all()

    if not plate_number or not camera_id:
        return jsonify({"message": "Missing plate number or camera ID"}), 400

    normalized_plate_number = plate_number.upper()

    # Validate the camera ID and its type
    camera = Camera.query.get(camera_id)
    if not camera or camera.camera_type != 'Entrance/Exit':
        return jsonify({"message": "Invalid camera"}), 400

    # Find the closest matching plate number in the Vehicle table
    vehicles = registered_vehicles
    closest_match = None
    min_distance = float('inf')

    for vehicle in vehicles:
        db_plate_number = vehicle.plate_number.upper()
        distance = levenshtein_distance(normalized_plate_number, db_plate_number)
        if distance < min_distance:
            min_distance = distance
            closest_match = vehicle

    # Allow only matches within a threshold (e.g., 2 character changes)
    if closest_match and min_distance <= 2:
        normalized_plate_number = closest_match.plate_number.upper()
        identity = closest_match.identity  # Retrieve identity if available
        username = closest_match.username
        email = closest_match.email
    else:
        new_log = VehicleLog(
            plate_number=plate_number,
            time_in=datetime.now(manila_timezone)
        )
        db.session.add(new_log)
        db.session.commit()

        send_info_notification(
            plate_number_param=plate_number,
            identity_param=None,
            username_param=None,
            email_param=None,
            time_in_param=format_datetime_to_manila(new_log.time_in),
            time_out_param=None,
            error_param=None
        )
        return jsonify({"message": "Plate number not registered"}), 200

    # Check for any recent log for the same plate within 60 seconds
    recent_log = VehicleLog.query.filter(
        func.upper(VehicleLog.plate_number) == normalized_plate_number,
        (VehicleLog.time_in >= datetime.now(manila_timezone) - timedelta(seconds=120)) |
        (VehicleLog.time_out >= datetime.now(manila_timezone) - timedelta(seconds=120))
    ).first()

    if recent_log:
        return jsonify({"message": "Recent log exists"}), 409

    # Check for an existing log without a time_out
    existing_log = VehicleLog.query.filter(
        func.upper(VehicleLog.plate_number) == normalized_plate_number,
        VehicleLog.time_out.is_(None)
    ).first()

    if existing_log:
        # Update the existing log with a new time_out
        existing_log.time_out = datetime.now(manila_timezone)
        db.session.commit()

        # Trigger the send_info_notification for time_out
        send_info_notification(
            plate_number_param=normalized_plate_number,
            username_param=username,
            email_param=email,
            identity_param=identity,
            time_in_param=format_datetime_to_manila(existing_log.time_in),
            time_out_param=format_datetime_to_manila(existing_log.time_out),
            error_param=None
        )
        return jsonify({"message": "Log updated"}), 200

    # Check for the count of logs with the same identity and no time_out
    identity_limits = {
        "Visitor": 5,
        "ILSparent": 2,
        "Dropoff": 2
    }

    if identity in identity_limits:
        current_count = VehicleLog.query.filter(
            VehicleLog.identity == identity,
            VehicleLog.time_out.is_(None)
        ).count()

        if current_count >= identity_limits[identity]:
            send_info_notification(None, None, None, None, None, f"The space for the {identity} has already reach the limit")
            return jsonify({"message": "error" ,"error": f"The space for the {identity} has already reach the limit"}), 201

    # Create a new log with time_in
    new_log = VehicleLog(
        plate_number=normalized_plate_number,
        username=username,
        email=email,
        identity=identity,
        time_in=datetime.now(manila_timezone)
    )
    db.session.add(new_log)
    db.session.commit()

    # Trigger the send_info_notification for time_in
    send_info_notification(
        plate_number_param=normalized_plate_number,
        username_param=username,
        email_param=email,
        identity_param=identity,
        time_in_param=format_datetime_to_manila(new_log.time_in),
        time_out_param=None,
        error_param=None
    )
    return jsonify({"message": "Log created"}), 201

@vehiclelog_controller.route('/archive-log', methods=['POST'])
def archive_logs():
    filter_date = request.json.get('filter_date')
    date = datetime.strptime(filter_date, '%Y-%m-%d')

    logs_to_archive = VehicleLog.query.filter(func.date(VehicleLog.time_in) == date.date()).all()

    archive_data = [
        ArchiveLog(
            log_id=log.log_id,
            plate_number=log.plate_number,
            username=log.username,
            identity=log.identity,
            time_in=log.time_in,
            time_out=log.time_out
        ) for log in logs_to_archive
    ]

    if archive_data:
        db.session.bulk_save_objects(archive_data)
        VehicleLog.query.filter(func.date(VehicleLog.time_in) == date.date()).delete()
        db.session.commit()

    return jsonify({"message": "success"})

@vehiclelog_controller.route('/restore-logs', methods=['POST'])
def restore_logs():
    filter_date = request.json.get('filter_date')
    date = datetime.strptime(filter_date, '%Y-%m')

    archive_logs = ArchiveLog.query.filter(
        func.extract('year', ArchiveLog.time_in) == date.year,
        func.extract('month', ArchiveLog.time_in) == date.month
    ).all()

    logs_data = [
        VehicleLog(
            log_id=log.log_id,
            plate_number=log.plate_number,
            username=log.username,
            identity=log.identity,
            time_in=log.time_in,
            time_out=log.time_out
        ) for log in archive_logs
    ]

    if logs_data:
        db.session.bulk_save_objects(logs_data)
        ArchiveLog.query.filter(
            func.extract('year', ArchiveLog.time_in) == date.year,
            func.extract('month', ArchiveLog.time_in) == date.month
        ).delete()
        db.session.commit()

    return jsonify({"message": "success"})

@vehiclelog_controller.route('/vehicle-count', methods=['GET'])
def get_vehicle_count():
    try:
        # Get the current date in Manila timezone
        today = datetime.now(manila_timezone).date()

        # Query to count vehicles grouped by identity for today's logs without a time_out
        counts = db.session.query(
            VehicleLog.identity,
            func.count(VehicleLog.identity).label('count')
        ).filter(
            func.date(VehicleLog.time_in) == today,  # Filter logs for today's date
            VehicleLog.time_out.is_(None)  # Include only logs with no time_out
        ).group_by(VehicleLog.identity).all()

        # Convert query result to a dictionary
        vehicle_counts = {
            (identity if identity is not None else "Unknown"): count
            for identity, count in counts
        }

        # Add missing identities with zero count
        identities = ["Employee", "Visitor", "Dropoff", "ILSparent"]
        for identity in identities:
            if identity not in vehicle_counts:
                vehicle_counts[identity] = 0

        return jsonify({"vehicleCounts": vehicle_counts}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@vehiclelog_controller.route('/fetch-visitors', methods=['GET'])
def get_visitors():
    try:
        # Query to fetch all Visitor vehicle logs with no time_out
        visitor_logs = VehicleLog.query.filter(
            and_(
                VehicleLog.identity == "Visitor",  # Identity must be Visitor
                VehicleLog.time_out.is_(None)      # time_out must be None
            )
        ).all()

        # Check if there are no results
        if not visitor_logs:
            return jsonify({"visitors": []}), 200

        # Convert the query results into a list of dictionaries for JSON response
        visitor_data = [
            {
                "log_id": log.log_id,
                "plate_number": log.plate_number,
                "owner_name": log.username,
                "identity": log.identity,
            }
            for log in visitor_logs
        ]

        return jsonify({"visitors": visitor_data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@vehiclelog_controller.route('/fetch-drops', methods=['GET'])
def get_dropoffs():
    try:
        time_threshold = datetime.now(manila_timezone) - timedelta(minutes=2)
        # Query to fetch all Visitor vehicle logs with no time_out
        dropoff_logs = VehicleLog.query.filter(
            and_(
                VehicleLog.identity == "Dropoff",  # Identity must be Visitor
                VehicleLog.time_out.is_(None),     # time_out must be None
                VehicleLog.time_in <= time_threshold
            )
        ).all()

        # Check if there are no results
        if not dropoff_logs:
            return jsonify({"dropoffs": []}), 200

                # Convert the query results into a list of dictionaries for JSON response
        dropoff_data = [
            {
                "log_id": log.log_id,
                "plate_number": log.plate_number,
                "owner_name": log.username,
                "identity": log.identity,
            }
            for log in dropoff_logs
        ]

        return jsonify({"dropoffs": dropoff_data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@vehiclelog_controller.route('/update-log', methods=['POST'])
def update_log():
    data = request.get_json()
    plate_number = data.get('plate_number')
    identity = data.get('identity')

    try:
        # Find the vehicle log by plate_number
        vehicle_log = VehicleLog.query.filter_by(plate_number=plate_number).first()
        if not vehicle_log:
            existing_vehicle = Vehicle.query.filter_by(plate_number=plate_number).first()

            if existing_vehicle:
                # If the vehicle already exists, update its identity and status
                existing_vehicle.identity = identity
                existing_vehicle.status = "Accepted"
                db.session.commit()
            else:
                # If the vehicle doesn't exist, create a new entry
                new_vehicle = Vehicle(
                    plate_number=plate_number,
                    identity=identity,
                    status="Accepted"
                )
                db.session.add(new_vehicle)
                db.session.commit()
        else:
            # Update the fields in the log
            vehicle_log.identity = identity

             # Commit the changes to the database
            db.session.commit()

        new_vehicle = Vehicle(
            plate_number=plate_number,
            identity=identity,
            status="Accepted"
        )

        db.session.add(new_vehicle)
        db.session.commit()

        # Delete all records in VehicleLog that have no username and identity
        VehicleLog.query.filter(
            (VehicleLog.identity == None)
        ).delete()
        db.session.commit()

        return jsonify({"message": "Log updated successfully"}), 200
    except Exception as e:
        db.session.rollback()  # Rollback changes in case of an error
        return jsonify({"error": str(e)}), 500
    
@vehiclelog_controller.route('/delete-log', methods=['POST'])
def delete_logs():
    # Delete all records in VehicleLog that have no username and identity
    VehicleLog.query.filter(
        (VehicleLog.identity == None)
    ).delete()
    db.session.commit()
    
    return jsonify({"message": "Log updated successfully"}), 200
