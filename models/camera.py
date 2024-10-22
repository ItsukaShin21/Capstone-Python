from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Camera(Base):
    __tablename__ = 'cameras'

    id = Column(Integer, primary_key=True, autoincrement=True)
    camera_name = Column(String, nullable=False)
    rtsp_url = Column(String, nullable=False)
    location = Column(String, nullable=False)
    camera_type = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Camera(name={self.camera_name}, location={self.location}, type={self.camera_type})>"