from flask import Flask
from flask_cors import CORS
from routes.camera_routes import camera_bp
from routes.video_routes import video_bp
from routes.background_task import background_task_bp, background_task
import threading

# Initialize the Flask application
app = Flask(__name__)

# Enable CORS for all routes
CORS(app, resources={r"/cameras": {"origins": "*"}})

# Register blueprints
app.register_blueprint(camera_bp)
app.register_blueprint(video_bp)
app.register_blueprint(background_task_bp)

# Run the application
if __name__ == '__main__':
    thread = threading.Thread(target=background_task, args=(9,), daemon=True)
    thread.start()

    if thread.is_alive():
        print("Background task thread is running.")
    else:
        print("Background task thread failed to start.")
        
    app.run(host='0.0.0.0', port=5000, debug=True)