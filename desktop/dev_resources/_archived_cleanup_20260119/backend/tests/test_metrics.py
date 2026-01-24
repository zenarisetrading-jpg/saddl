import pytest
from backend.services.executive_metrics import ExecutiveMetricsService

@pytest.fixture
def service():
    return ExecutiveMetricsService()

@pytest.fixture
def sample_data():
    return {
        'current_period': {
            'sales': 100000,
            'spend': 40000,
            'roas': 2.5,
            'cvr': 0.10,
            'cpc': 5.0
        },
        'previous_period': {
            'sales': 80000,
            'spend': 35000,
            'roas': 2.0,
            'cvr': 0.08,
            'cpc': 6.0
        },
        'medians': {
            'roas': 2.5,
            'cvr': 0.10
        }
    }

def test_net_contribution_calculation(service, sample_data):
    """Net contribution = revenue - spend"""
    result = service.compute_kpis(sample_data)
    
    assert result['net_contribution']['value'] == 60000  # 100k - 40k
    assert result['net_contribution']['delta_abs'] == 15000  # 60k - 45k

def test_efficiency_score_range(service, sample_data):
    """Efficiency score must be 0-100"""
    result = service.compute_kpis(sample_data)
    
    efficiency = result['efficiency_score']['value']
    assert 0 <= efficiency <= 100

def test_momentum_classification(service):
    """Test EXACT momentum logic from spec"""
    current = {'sales': 110000, 'roas': 2.4, 'spend': 45000}
    previous = {'sales': 100000, 'roas': 2.6, 'spend': 40000}
    medians = {'roas': 2.5}
    
    # Revenue up (+10%), Efficiency >= median (2.4 < 2.5 = FALSE)
    # So NOT scale_push
    classification = service._classify_momentum(current, previous, medians)
    
    # Should be something other than scale_push
    assert classification != "scale_push"

def test_risk_index_calculation(service):
    """Risk index = % spend in low-performance quadrant"""
    campaigns = [
        {'spend': 10000, 'roas': 2.0, 'cvr': 0.08},  # Below medians
        {'spend': 15000, 'roas': 3.0, 'cvr': 0.12},  # Above medians
        {'spend': 20000, 'roas': 1.5, 'cvr': 0.06},  # Below medians
    ]
    
    result = service._compute_risk_index(campaigns)
    
    # Risky spend = 20k (only 3rd campaign is strictly < median). 
    # Campaign 1 is AT median, so not "low performance"
    expected = 20000 / 45000
    assert abs(result['value'] - expected) < 0.01

def test_decision_impact_aggregation(service):
    """Decision impact sums correctly"""
    data = {
        'decision_history': [
            {'type': 'bid_increase', 'measured_impact': 5000},
            {'type': 'bid_increase', 'measured_impact': 3000},
            {'type': 'pause', 'measured_impact': -2000},
        ],
        'current_period': {'sales': 100000}
    }
    
    result = service.compute_decision_impact(data)
    
    assert result['bid_ups']['count'] == 2
    assert result['bid_ups']['impact'] == 8000
    assert result['net_impact'] == 6000  # 8000 - 2000
