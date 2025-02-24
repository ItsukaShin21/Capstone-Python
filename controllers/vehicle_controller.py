from flask import Blueprint, request, jsonify, abort, send_from_directory
from werkzeug.utils import secure_filename
from datetime import datetime
from pathlib import Path
from models.vehicle import Vehicle
from extensions import db
import os
from pytz import timezone

manila_timezone = timezone('Asia/Manila')

vehicle_controller = Blueprint('vehicle_controller', __name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def save_file(file, folder):
    if file:
        filename = secure_filename(file.filename)
        path = os.path.join(folder, filename)
        file.save(path)
        return path
    return None

# View Image
@vehicle_controller.route('/uploads/<path:filename>')
def uploaded_file(filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        return abort(404, description="File not found")
    return send_from_directory(UPLOAD_FOLDER, filename)

# Vehicle Register (Admin/CSO)
@vehicle_controller.route('/vehicle-register', methods=['POST'])
def register_vehicle():
    data = request.json

    required_fields = ["plate_number", "username", "identity", "email"]
    for field in required_fields:
        if field not in data:
            return jsonify({"message": f"{field} is required"})

    if Vehicle.query.filter_by(plate_number=data['plate_number']).first():
        return jsonify({"message": "plate number is used"})

    vehicle = Vehicle(
        username=data['username'],
        plate_number=data['plate_number'],
        identity=data['identity'],
        email=data['email'],
        valid_id_url="null",
        license_doc_url="null",
        status="Accepted",
    )

    db.session.add(vehicle)
    db.session.commit()
    return jsonify({"message": "success"})

# Vehicle Register (Vehicle Owner)
@vehicle_controller.route('/vehicle-register-request', methods=['POST'])
def register_request():
    required_fields = ["plate_number", "username", "identity", "email"]

    for field in required_fields:
        if field not in request.form:
            return jsonify({"message": f"{field} is required"})
        
    plate_number = request.form['plate_number']
    existing_vehicle = Vehicle.query.filter_by(plate_number=plate_number).first()

    if existing_vehicle:
        return jsonify({"message": "Plate Used"})

    valid_id_url = save_file(request.files.get('valid_id_url'), UPLOAD_FOLDER)
    license_doc_url = save_file(request.files.get('license_doc_url'), UPLOAD_FOLDER)

    vehicle = Vehicle(
        plate_number=request.form['plate_number'],
        username=request.form['username'],
        identity=request.form['identity'],
        email=request.form['email'],
        valid_id_url=valid_id_url,
        license_doc_url=license_doc_url,
        status="Pending",
    )

    db.session.add(vehicle)
    db.session.commit()
    return jsonify({"message": "success"})

# Fetch all Vehicles
@vehicle_controller.route('/fetch-vehicles', methods=['GET'])
def display_vehicles():
    vehicles = Vehicle.query.filter_by(status='Accepted').all()
    vehicle_list = [vehicle.as_dict() for vehicle in vehicles]
    return jsonify({"vehicleList": vehicle_list})

# Fetch a specific vehicle with details
@vehicle_controller.route('/fetch-vehicle/<string:vehicle_id>', methods=['GET'])
def display_vehicle(vehicle_id):
    vehicle = Vehicle.query.get(vehicle_id)
    if vehicle:
        return jsonify({"vehicleDetails": vehicle.as_dict()})
    return jsonify({"message": "Vehicle not found"})

# Fetch all pending request
@vehicle_controller.route('/fetch-requests', methods=['GET'])
def fetch_pendings():
    pending_list = Vehicle.query.filter_by(status='Pending').all()
    pendings = [vehicle.as_dict() for vehicle in pending_list]
    return jsonify({"pendingList": pendings})

# Fetch a specific request with details
@vehicle_controller.route('/fetch-pending/<string:plate_number>', methods=['GET'])
def fetch_pending_detail(plate_number):
    pending = Vehicle.query.filter_by(plate_number=plate_number).first()
    if pending:
        return jsonify({"pendingDetails": pending.as_dict()})
    return jsonify({"message": "Vehicle not found"})

# Vehicle update
@vehicle_controller.route('/update-vehicle', methods=['POST'])
def update_vehicle():
    data = request.json

    required_fields = ["plate_number", "username", "identity"]
    for field in required_fields:
        if field not in data:
            return jsonify({"message": f"{field} is required"})

    vehicle = Vehicle.query.filter_by(plate_number=data['plate_number']).first()
    if vehicle:
        vehicle.username = data['username']
        vehicle.identity = data['identity']
        db.session.commit()
        return jsonify({"message": "success"})

    return jsonify({"message": "Vehicle not found"})

# Request accept
@vehicle_controller.route('/accept-request', methods=['POST'])
def accept_request():
    data = request.json

    if 'plate_number' not in data:
        return jsonify({"message": "plate_number is required"})

    vehicle = Vehicle.query.filter_by(plate_number=data['plate_number']).first()
    if vehicle:
        vehicle.status = "Accepted"
        vehicle.valid_id_url = "null"
        vehicle.license_doc_url = "null"
        db.session.commit()
        return jsonify({"message": "success"})

    return jsonify({"message": "Vehicle not found"})

# Vehicle delete
@vehicle_controller.route('/delete-vehicle', methods=['POST'])
def delete_vehicle():
    data = request.json

    if 'plate_number' not in data:
        return jsonify({"message": "plate_number is required"})

    vehicle = Vehicle.query.filter_by(plate_number=data['plate_number']).first()
    if vehicle:
        db.session.delete(vehicle)
        db.session.commit()
        return jsonify({"message": "success"})

    return jsonify({"message": "Vehicle not found"})

@vehicle_controller.route('/check-vehicle-exists/<string:plate_number>', methods=['GET'])
def check_vehicle_exists(plate_number):
    vehicle = Vehicle.query.filter_by(plate_number=plate_number).first()
    if vehicle:
        return jsonify({"Identity": vehicle.identity or "No record"})

    return jsonify({"Identity": "No record"})

@vehicle_controller.route('/check-accounts', methods=['POST'])
def check_accounts():
    try:
        # Get the current date and time in Manila timezone
        current_time = datetime.now(manila_timezone)

        # Query all vehicles those with identity "Visitor"
        vehicles = Vehicle.query.filter(Vehicle.identity == "Visitor").all()

        # Loop through the vehicles and check their created_at date
        for vehicle in vehicles:
            if vehicle.created_at:
                # Make vehicle.created_at timezone-aware
                if vehicle.created_at.tzinfo is None:
                    vehicle_created_at = manila_timezone.localize(vehicle.created_at)
                else:
                    vehicle_created_at = vehicle.created_at

                # Calculate the time difference
                time_difference = current_time - vehicle_created_at
                
                # Check if more than 1 day (24 hours) has passed
                if time_difference.total_seconds() > 24 * 60 * 60:  # 24 hours in seconds
                    db.session.delete(vehicle)

        # Commit the changes to the database
        db.session.commit()
        return jsonify({"message": "Outdated vehicles deleted successfully."})

    except Exception as e:
        # Handle any unexpected errors
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500