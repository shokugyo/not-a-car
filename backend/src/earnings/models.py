from sqlalchemy import Column, Integer, Float, DateTime, String, Enum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from src.database import Base
from src.vehicles.models import VehicleMode


class Earning(Base):
    __tablename__ = "earnings"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("owners.id"), nullable=False)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)

    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="JPY")
    mode = Column(Enum(VehicleMode), nullable=False)

    # Details
    description = Column(String(500))
    reference_id = Column(String(100))
    reference_type = Column(String(50))

    # Time info
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    duration_minutes = Column(Integer)

    # Fees
    platform_fee = Column(Float, default=0)
    net_amount = Column(Float)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    owner = relationship("Owner", back_populates="earnings")
    vehicle = relationship("Vehicle", back_populates="earnings")
