from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, Text
from .database import Base

class Reading(Base):
    __tablename__ = "readings"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    species = Column(String, index=True, default="Shrimp")
    temperature = Column(Float)
    turbidity = Column(Float)
    dissolved_oxygen = Column(Float)
    bod = Column(Float, nullable=True)
    co2 = Column(Float, nullable=True)
    ph = Column(Float)
    alkalinity = Column(Float, nullable=True)
    hardness = Column(Float, nullable=True)
    calcium = Column(Float, nullable=True)
    ammonia = Column(Float)
    nitrite = Column(Float, nullable=True)
    phosphorus = Column(Float, nullable=True)
    h2s = Column(Float, nullable=True)
    plankton = Column(Float, nullable=True)
    nitrate = Column(Float, nullable=True)
    salinity = Column(Float, nullable=True)
    is_simulated = Column(Boolean, default=False)

class PredictionRecord(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    reading_id = Column(Integer, nullable=True)
    species = Column(String)
    ml_prediction = Column(String)
    pollution_index = Column(Float)
    anomaly_flag = Column(Boolean, default=False)
    anomaly_score = Column(Float, default=0.0)
    trend_flag = Column(Boolean, default=False)
    trend_explanation = Column(String, nullable=True)
    final_classification = Column(String) # SAFE, MODERATE, CRITICAL
    explanation = Column(Text)
    recommendations_json = Column(Text)

class AlertRecord(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    species = Column(String)
    severity = Column(String) # MODERATE, CRITICAL
    parameter = Column(String)
    value = Column(Float)
    reason = Column(String)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    farm_name = Column(String, nullable=True)
    hashed_password = Column(String)
    role = Column(String, default="farmer") # farmer or admin
    created_at = Column(DateTime, default=datetime.utcnow)

class Pond(Base):
    __tablename__ = "ponds"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, nullable=True) # User ID
    name = Column(String) # e.g. Pond A - Shrimp
    species = Column(String, default="Shrimp") # Shrimp, Tilapia, Carp
    created_at = Column(DateTime, default=datetime.utcnow)

class SpeciesProfileRecord(Base):
    __tablename__ = "species_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    config_json = Column(Text)

class SimulationStateRecord(Base):
    __tablename__ = "simulation_state"

    id = Column(Integer, primary_key=True, index=True)
    is_running = Column(Boolean, default=False)
    current_index = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow)

