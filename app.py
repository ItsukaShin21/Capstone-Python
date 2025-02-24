from flask import Flask
from flask_cors import CORS
from extensions import db
from controllers.camera_controller import camera_controller
from controllers.user_controller import user_controller
from controllers.vehicle_controller import vehicle_controller
from controllers.vehiclelog_controller import vehiclelog_controller
from routes.video_routes import video_bp
from utils.alarm_utils import alarm_bp, send_info_bp

# Initialize the Flask application
app = Flask(__name__)

# Configurations
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:@127.0.0.1:3306/capstone_db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Enable CORS for all routes
CORS(app, 
     supports_credentials=True,
     resources={r"/*": { # "origins": "http://localhost:3000"
                        "origins": "https://lnu-vms.online"
                        }})

# Register blueprints
app.register_blueprint(vehicle_controller)
app.register_blueprint(user_controller)
app.register_blueprint(camera_controller)
app.register_blueprint(vehiclelog_controller)
app.register_blueprint(alarm_bp)
app.register_blueprint(video_bp)
app.register_blueprint(send_info_bp)

# Run the application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)