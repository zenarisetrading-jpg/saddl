import pytest
from pydantic import ValidationError
from backend.models.executive_schemas import ExecutiveDashboard, KPIMetric, MomentumDataPoint, DecisionCategory, DecisionImpact, PerformanceBreakdown

def test_kpi_metric_valid():
    """Valid KPI metric passes validation"""
    kpi = KPIMetric(
        value=100,
        delta_pct=5.0,
        delta_abs=5.0,
        trend="up"
    )
    assert kpi.value == 100
    assert kpi.trend == "up"

def test_kpi_metric_invalid_trend():
    """Invalid trend value raises error"""
    with pytest.raises(ValidationError):
        KPIMetric(
            value=100,
            delta_pct=5.0,
            delta_abs=5.0,
            trend="invalid"  # Should be "up", "down", or "stable"
        )

def test_dashboard_structure():
    """Full dashboard validates correctly"""
    data = {
        "kpis": {
            "revenue": {"value": 100, "delta_pct": 5.0, "delta_abs": 5.0, "trend": "up"},
            "net_contribution": {"value": 50, "delta_pct": 3.0, "delta_abs": 1.5, "trend": "up"},
            "efficiency_score": {"value": 82, "delta_pct": 2.0, "delta_abs": 1.6, "trend": "up"},
            "risk_index": {"value": 0.18, "delta_pct": -10.0, "delta_abs": -0.02, "trend": "down"},
            "scale_headroom": {"value": 0.42, "delta_pct": 5.0, "delta_abs": 0.02, "trend": "up"}
        },
        "momentum": [],
        "decision_impact": {
            "period": "Last 14 Days",
            "net_impact": 10000,
            "net_impact_pct": 5.0,
            "bid_ups": {"count": 10, "impact": 5000, "type": "promote", "detail": "test"},
            "bid_downs": {"count": 5, "impact": -2000, "type": "prevent", "detail": "test"},
            "pauses": {"count": 3, "impact": -1000, "type": "prevent", "detail": "test"},
            "negatives": {"count": 8, "impact": 8000, "type": "prevent", "detail": "test"}
        },
        "performance": {
            "quadrant_data": [],
            "revenue_by_match_type": {},
            "spend_distribution": {},
            "cost_efficiency_scatter": []
        },
        "metadata": {}
    }
    
    dashboard = ExecutiveDashboard(**data)
    assert dashboard.kpis.revenue.value == 100
