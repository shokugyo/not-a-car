from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from src.database import Base


class VehicleMode(str, enum.Enum):
    IDLE = "idle"
    ACCOMMODATION = "accommodation"
    DELIVERY = "delivery"
    RIDESHARE = "rideshare"
    MAINTENANCE = "maintenance"
    CHARGING = "charging"
    TRANSIT = "transit"


class InteriorMode(str, enum.Enum):
    STANDARD = "standard"
    BED = "bed"
    CARGO = "cargo"
    OFFICE = "office"
    PASSENGER = "passenger"


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("owners.id"), nullable=False)

    # Basic info
    name = Column(String(100))
    license_plate = Column(String(20), unique=True, index=True)
    model = Column(String(100))
    year = Column(Integer)
    vin = Column(String(17), unique=True)

    # Status
    current_mode = Column(Enum(VehicleMode), default=VehicleMode.IDLE)
    interior_mode = Column(Enum(InteriorMode), default=InteriorMode.STANDARD)
    is_active = Column(Boolean, default=True)
    is_available = Column(Boolean, default=True)

    # Location
    latitude = Column(Float, default=35.6762)  # Tokyo default
    longitude = Column(Float, default=139.6503)
    last_location_update = Column(DateTime, default=datetime.utcnow)

    # Battery/Fuel
    battery_level = Column(Float, default=100.0)
    range_km = Column(Float, default=400.0)

    # Settings
    allowed_modes = Column(JSON, default=["accommodation", "delivery", "rideshare"])
    auto_mode_switch = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Current task tracking
    current_hourly_rate = Column(Float, default=0.0)
    mode_started_at = Column(DateTime)
    today_earnings = Column(Float, default=0.0)

    # Relationships
    owner = relationship("Owner", back_populates="vehicles")
    earnings = relationship("Earning", back_populates="vehicle", lazy="selectin")
    schedules = relationship("VehicleSchedule", back_populates="vehicle", lazy="selectin")


class VehicleSchedule(Base):
    __tablename__ = "vehicle_schedules"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)

    day_of_week = Column(Integer)  # 0-6 (Mon-Sun)
    start_time = Column(String(5))  # "09:00"
    end_time = Column(String(5))    # "18:00"
    allowed_mode = Column(Enum(VehicleMode))
    priority = Column(Integer, default=0)

    is_active = Column(Boolean, default=True)

    vehicle = relationship("Vehicle", back_populates="schedules")
