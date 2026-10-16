from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
    true,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.domains.workspaces.models import Workspace


class MetricType(str, enum.Enum):
    counter = "counter"
    gauge = "gauge"
    percentage = "percentage"
    currency = "currency"


class Metric(Base):
    __tablename__ = "metrics"
    __table_args__ = (
        UniqueConstraint("workspace_id", "name", name="uq_metrics_workspace_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text)
    unit: Mapped[str | None] = mapped_column(String(32))
    type: Mapped[MetricType] = mapped_column(
        Enum(MetricType, name="metric_type"),
        default=MetricType.gauge,
        server_default=MetricType.gauge.value,
    )
    is_active: Mapped[bool] = mapped_column(default=True, server_default=true())
    config: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    workspace: Mapped[Workspace] = relationship(back_populates="metrics")
    data_points: Mapped[list[MetricDataPoint]] = relationship(
        back_populates="metric", cascade="all, delete-orphan", passive_deletes=True
    )


class MetricDataPoint(Base):
    """Tabela de maior volume do sistema (série temporal)."""

    __tablename__ = "metric_data_points"
    # Índice composto: serve a consulta dominante (metric_id + intervalo de tempo).
    # Um índice só em `timestamp` não atende essa consulta e custa escrita.
    __table_args__ = (Index("ix_metric_data_points_metric_ts", "metric_id", "timestamp"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    metric_id: Mapped[int] = mapped_column(ForeignKey("metrics.id", ondelete="CASCADE"))
    value: Mapped[float] = mapped_column(Float)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    # `metadata` é nome reservado do Declarative. Nullable de propósito:
    # evita gravar "{}" em milhões de linhas.
    meta: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    metric: Mapped[Metric] = relationship(back_populates="data_points")
