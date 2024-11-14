import requests
from config import API_URL

def log_plate_number(plate_number, camera_id):
    try:
        data = {'plate_number': plate_number, 'camera_id': camera_id}
        response = requests.post(f"{API_URL}/add-record-log", json=data)
        
        if response.status_code == 200:
            print(f"Successfully logged plate number: {plate_number}")
        else:
            print(f"Failed to log plate number: {plate_number}, Problem : {response.text}")
    
    except requests.exceptions.RequestException as e:
        print(f"Error logging plate number: {e}")


def get_plate_identity(plate_number, registered_vehicles):
    for entry in registered_vehicles:
        if entry["plate_number"] == plate_number:
            return entry["identity"]
    return "Unregistered"