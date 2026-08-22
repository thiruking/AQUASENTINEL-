from pydantic import BaseModel, ConfigDict, Field
from typing import List, Dict, Optional, Any
from datetime import datetime

class WaterReadingInput(BaseModel):
    species: str = Field(default="Shrimp", description="Species: Shrimp, Tilapia, or Carp")
    temperature: float = Field(default=28.5)
    turbidity: float = Field(default=35.0)
    dissolved_oxygen: float = Field(default=6.5, alias="DO")
    bod: Optional[float] = Field(default=4.0)
    co2: Optional[float] = Field(default=5.0)
    ph: float = Field(default=7.8)
    alkalinity: Optional[float] = Field(default=120.0)
    hardness: Optional[float] = Field(default=150.0)
    calcium: Optional[float] = Field(default=60.0)
    ammonia: float = Field(default=0.02)
    nitrite: Optional[float] = Field(default=0.05)
    phosphorus: Optional[float] = Field(default=0.1)
    h2s: Optional[float] = Field(default=0.002)
    plankton: Optional[float] = Field(default=45000.0)
    nitrate: Optional[float] = Field(default=5.0)
    salinity: Optional[float] = Field(default=15.0)

    model_config = ConfigDict(populate_by_name=True)

class ParameterContribution(BaseModel):
    parameter: str
    contribution_percent: float
    status: str # Optimal, Warning, Critical
    current_value: float
    ideal_range: str

class PredictionResponse(BaseModel):
    timestamp: datetime
    species: str
    ml_prediction: str
    pollution_index: float
    anomaly_flag: bool
    anomaly_score: float
    trend_flag: bool
    trend_explanation: Optional[str] = None
    final_classification: str # SAFE, MODERATE, CRITICAL
    explanation: str
    parameter_contributions: List[ParameterContribution]
    feature_importances: Dict[str, float]
    recommendations: List[str]
    traditional_classification: str
    traditional_reason: str

class AlertSchema(BaseModel):
    id: int
    timestamp: datetime
    species: str
    severity: str
    parameter: str
    value: float
    reason: str

class ModelMetricSchema(BaseModel):
    model_name: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    is_best: bool = False

class SimulationStatusResponse(BaseModel):
    is_running: bool
    current_index: int
    total_records: int
    latest_prediction: Optional[PredictionResponse] = None

class UserRegisterInput(BaseModel):
    name: str
    email: str
    password: str
    farm_name: Optional[str] = "Coastal Aqua Farm"
    role: Optional[str] = "farmer"

class UserLoginInput(BaseModel):
    email: str
    password: str
    remember_me: Optional[bool] = False

class UserResponse(BaseModel):
    # SQLAlchemy model instances are returned by the registration endpoint.
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    farm_name: Optional[str] = None
    role: str
    created_at: datetime

class PondCreateInput(BaseModel):
    name: str
    species: str = "Shrimp"

class PondResponse(BaseModel):
    # SQLAlchemy model instances are returned by the pond creation endpoint.
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: Optional[int] = None
    name: str
    species: str
    created_at: datetime

