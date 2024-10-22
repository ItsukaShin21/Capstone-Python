# Configuration file
from sqlalchemy import create_engine

API_URL = 'http://192.168.1.42:8000/api'

# MySQL database connection URI
DATABASE_URI = 'mysql+mysqlconnector://root:@192.168.0.113:3306/capstone_db'

# Create the engine
engine = create_engine(DATABASE_URI)