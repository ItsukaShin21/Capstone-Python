import requests
import Levenshtein
from datetime import datetime

def log_plate_number(plate_number, camera_id, registered_vehicles):
    try:
        # Define the URL for the Flask route
        # url = "http://localhost:5000/add-record-log"
        url = "https://api.lnu-vms.online/add-record-log"

        # Prepare the JSON payload
        payload = {
            "plate_number": plate_number,
            "camera_id": camera_id,
        }

        # Send the POST request with JSON data
        response = requests.post(url, json=payload)

        # Process the response
        if response.status_code == 200:
            print(f"Success: {response.json().get('message')}")
        elif response.status_code == 201:
            print(f"Created: {response.json().get('message')}")
        else:
            print(f"Error: {response.status_code} - {response.json().get('message')}")

    except requests.exceptions.RequestException as e:
        print(f"Request error: {str(e)}")
    except Exception as e:
        print(f"Internal error: {str(e)}")

def get_plate_identity(plate_number, registered_vehicles, threshold=0.5):
    closest_match = None
    highest_similarity = 0.5
    
    # Normalize the detected plate by removing spaces
    normalized_plate_number = plate_number.replace(" ", "").upper()
    print(f"Normalized Detected Plate: {normalized_plate_number}")
    # print(registered_vehicles)

    for entry in registered_vehicles:
        # Normalize the registered plate by removing spaces
        registered_plate = entry["plate_number"].replace(" ", "").upper()
        # print(f"Comparing with Registered Plate: {registered_plate}")
        
        # Calculate similarity as 1 - normalized Levenshtein distance
        similarity = 1 - (Levenshtein.distance(normalized_plate_number, registered_plate) / max(len(normalized_plate_number), len(registered_plate)))
        # print(f"Similarity with {registered_plate}: {similarity}")

        if similarity > highest_similarity:
            highest_similarity = similarity
            closest_match = entry
    
    # Only return identity if similarity meets the threshold
    if closest_match and highest_similarity >= threshold:
        print(f"Match Found: {closest_match['plate_number']} with Similarity: {highest_similarity}")
        return closest_match.get("identity", "Unregistered")
    print("No match found.")
    return "Unregistered"