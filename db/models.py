from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class FarmProfile(Base):
    __tablename__ = 'farm_profiles'
    id = Column(Integer, primary_key=True)
    location = Column(String, default="Unknown")
    soil_type = Column(String, default="Unknown")
    main_crops = Column(String, default="Unknown")
    size = Column(String, default="Unknown")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Field(Base):
    __tablename__ = 'fields'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    crop = Column(String)
    planted_date = Column(DateTime)
    area = Column(Float)
    notes = Column(Text)
    logs = relationship("ActivityLog", back_populates="field")

class ActivityLog(Base):
    __tablename__ = 'activity_logs'
    id = Column(Integer, primary_key=True)
    field_id = Column(Integer, ForeignKey('fields.id'))
    date = Column(DateTime, default=datetime.utcnow)
    activity_type = Column(String)
    description = Column(Text)
    amount = Column(String)
    field = relationship("Field", back_populates="logs")

class MarketReport(Base):
    __tablename__ = 'market_reports'
    id = Column(Integer, primary_key=True)
    crop = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    unit = Column(String, default="kg")  # e.g., kg, bag, tonne
    location_county = Column(String, nullable=False) # e.g., 'Uasin Gishu', 'Nakuru'
    date = Column(DateTime, default=datetime.utcnow)
    reported_by = Column(String, nullable=True) # Farmer ID or 'system'
