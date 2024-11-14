from flask import Flask
from flask_cors import CORS
from routes.camera_routes import camera_bp
from routes.video_routes import video_bp
from utils.alarm_utils import alarm_bp

# Initialize the Flask application
app = Flask(__name__)

# Enable CORS for all routes
CORS(app)

# Register blueprints
app.register_blueprint(video_bp)
app.register_blueprint(alarm_bp)

# Run the application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)