# Configuration file
from sqlalchemy import create_engine

API_URL = 'http://192.168.254.117:8000/api'

# MySQL database connection URI
DATABASE_URI = 'mysql+mysqlconnector://root:@192.168.254.117:3306/capstone_db'

# Create the engine
engine = create_engine(DATABASE_URI,
                       pool_size=50,
                       max_overflow=200,
                       pool_recycle=1800)