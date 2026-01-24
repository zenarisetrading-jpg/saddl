"""
Executive Dashboard Data Schemas
PURE DATA CONTRACTS - No business logic here
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Literal, Optional
from datetime import datetime

class KPIMetric(BaseModel):
    """Single KPI with trend data"""
    value: float
    delta_pct: float  # vs previous period
    delta_abs: float
    trend: Literal["up", "down", "stable"]
    sparkline: List[float] = Field(default_factory=list)

class KPIs(BaseModel):
    """Top-level KPI metrics"""
    revenue: KPIMetric
    net_contribution: KPIMetric
    efficiency_score: KPIMetric  # 0-100 composite
    risk_index: KPIMetric  # 0-1 (display as %)
    scale_headroom: KPIMetric  # 0-1 (display as %)

class MomentumDataPoint(BaseModel):
    """Single time period in momentum chart"""
    date: str  # ISO format
    revenue: float
    spend_allocation: Dict[str, float]  # {classification: spend_amount}
    efficiency_line: float  # % vs baseline

class DecisionCategory(BaseModel):
    """Impact from one decision type"""
    count: int
    impact: float  # revenue impact (positive or negative)
    type: Literal["promote", "prevent", "protect"]
    detail: str

class DecisionImpact(BaseModel):
    """Overall decision impact summary"""
    period: str
    net_impact: float
    net_impact_pct: float
    bid_ups: DecisionCategory
    bid_downs: DecisionCategory
    pauses: DecisionCategory
    negatives: DecisionCategory

class QuadrantPoint(BaseModel):
    """Single point in performance scatter plot"""
    x: float  # CVR
    y: float  # ROAS
    size: float  # orders or spend
    label: str
    zone: Literal["scale", "optimize", "watch", "kill"]

class PerformanceBreakdown(BaseModel):
    """Performance analysis data"""
    quadrant_data: List[QuadrantPoint]
    revenue_by_match_type: Dict[str, float]
    spend_distribution: Dict[str, float]
    cost_efficiency_scatter: List[Dict]

class ExecutiveDashboard(BaseModel):
    """Complete executive dashboard payload"""
    kpis: KPIs
    momentum: List[MomentumDataPoint]
    decision_impact: DecisionImpact
    performance: PerformanceBreakdown
    metadata: Dict

    model_config = {
        "json_schema_extra": {
            "example": {
                "kpis": {
                    "revenue": {
                        "value": 224550,
                        "delta_pct": -45.8,
                        "delta_abs": -190000,
                        "trend": "down",
                        "sparkline": [200000, 210000, 215000, 224550]
                    },
                    # ... other KPIs
                },
                # ... rest of structure
            }
        }
    }
