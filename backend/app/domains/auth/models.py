import enum
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum, JSON, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class MetricType(str, enum.Enum):
    counter = "counter"
    gauge = "gauge"
    percentage = "percentage"
    currency = "currency"


class Metric(Base):
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    unit = Column(String, nullable=True)
    type = Column(Enum(MetricType), default=MetricType.gauge)
    is_active = Column(Boolean, default=True)
    config = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    workspace = relationship("Workspace", back_populates="metrics")
    data_points = relationship("MetricDataPoint", back_populates="metric", cascade="all, delete-orphan")


class MetricDataPoint(Base):
    __tablename__ = "metric_data_points"

    id = Column(Integer, primary_key=True)
    metric_id = Column(Integer, ForeignKey("metrics.id", ondelete="CASCADE"), nullable=False)
    value = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    metadata = Column(JSON, default={})

    metric = relationship("Metric", back_populates="data_points")