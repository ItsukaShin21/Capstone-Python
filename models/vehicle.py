from sqlalchemy import Column, String, Enum, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class VehicleStatus(enum.Enum):
    Pending = 'Pending'
    Accepted = 'Accepted'

class Vehicle(Base):
    __tablename__ = 'vehicles'

    plate_number = Column(String(255), primary_key=True)
    username = Column(String(255), nullable=False)
    identity = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    contact_number = Column(String(255), nullable=False)
    valid_id_url = Column(String, nullable=True)
    license_doc_url = Column(String, nullable=True)
    purpose = Column(String(255), nullable=False)
    status = Column(Enum(VehicleStatus), default=VehicleStatus.Pending)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Vehicle(plate_number={self.plate_number}, username={self.username}, status={self.status})>"