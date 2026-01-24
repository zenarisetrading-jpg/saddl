import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from backend.main import app

client = TestClient(app)

def test_endpoint_returns_200_with_valid_params():
    """Endpoint returns 200 with valid parameters"""
    response = client.get(
        "/api/executive/overview",
        params={
            "start_date": "2024-04-01T00:00:00",
            "end_date": "2024-04-21T00:00:00",
            "marketplace": "UAE Amazon",
            "granularity": "weekly"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Validate structure
    assert "kpis" in data
    assert "momentum" in data
    assert "decision_impact" in data
    assert "performance" in data

def test_endpoint_returns_400_with_invalid_dates():
    """Endpoint returns 400 when end_date before start_date"""
    response = client.get(
        "/api/executive/overview",
        params={
            "start_date": "2024-04-21T00:00:00",
            "end_date": "2024-04-01T00:00:00",  # Before start
        }
    )
    
    assert response.status_code == 400

def test_response_matches_schema():
    """Response matches Pydantic schema"""
    response = client.get(
        "/api/executive/overview",
        params={
            "start_date": "2024-04-01T00:00:00",
            "end_date": "2024-04-21T00:00:00",
        }
    )
    
    data = response.json()
    assert "kpis" in data
    assert "revenue" in data["kpis"]
    assert "value" in data["kpis"]["revenue"]
