"""
Executive Dashboard API Endpoint
READ-ONLY - No writes, no optimizer triggers
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from datetime import datetime
from typing import Literal

from ...models.executive_schemas import ExecutiveDashboard
from ...services.executive_metrics import ExecutiveMetricsService

# TODO: Import your actual data service/manager here. 
# For now, we'll assume a placeholder or hook into existing core logic if accessible.
# In the provided codebase, `core.data_hub.DataHub` seems to manage data.
# However, to avoid circular imports or strict coupling, we'll define a service interface.

router = APIRouter(prefix="/api/executive", tags=["executive"])

@router.get("/overview", response_model=ExecutiveDashboard)
async def get_executive_overview(
    start_date: datetime = Query(..., description="Start of analysis period"),
    end_date: datetime = Query(..., description="End of analysis period"),
    marketplace: str = Query("UAE Amazon", description="Marketplace filter"),
    granularity: Literal["daily", "weekly", "monthly"] = Query("weekly"),
    # Add auth dependency here
    # current_user: User = Depends(verify_token)
):
    """
    Executive dashboard overview.
    
    **IMPORTANT**: This endpoint is READ-ONLY and does NOT:
    - Trigger any optimizer actions
    - Make new Amazon Ads API calls
    - Write to database
    
    It only transforms existing cached data into executive-level insights.
    """
    
    # Validate date range
    if end_date <= start_date:
        raise HTTPException(status_code=400, detail="end_date must be after start_date")
    
    delta = end_date - start_date
    if delta.days > 90:
        raise HTTPException(status_code=400, detail="Date range cannot exceed 90 days")
    
    try:
        # Fetch existing cached data (no new API calls)
        # This part requires integrating with the existing `DataHub` or `PostgresManager`.
        # For the purpose of this file, we'll placeholder the data fetch 
        # as it depends on `core.data_hub` which might not be async or fully decoupled.
        
        # MOCK IMPLEMENTATION FOR ENDPOINT STRUCTURE VERIFICATION
        # In a real scenario, this would call: raw_data = await data_service.get_cached_metrics(...)
        
        raw_data = _mock_fetch_data(start_date, end_date, marketplace)
        
        if not raw_data:
            raise HTTPException(status_code=404, detail="No data found for this period")
        
        # Transform data using metrics service
        metrics_service = ExecutiveMetricsService()
        
        kpis = metrics_service.compute_kpis(raw_data)
        momentum = metrics_service.compute_momentum(raw_data, granularity)
        decision_impact = metrics_service.compute_decision_impact(raw_data)
        
        # Performance data (pass-through or simple transform)
        performance = {
            "quadrant_data": raw_data.get('quadrant_data', []),
            "revenue_by_match_type": raw_data.get('revenue_by_match_type', {}),
            "spend_distribution": raw_data.get('spend_distribution', {}),
            "cost_efficiency_scatter": raw_data.get('cost_efficiency_scatter', [])
        }
        
        return ExecutiveDashboard(
            kpis=kpis,
            momentum=momentum,
            decision_impact=decision_impact,
            performance=performance,
            metadata={
                "data_freshness": datetime.now().isoformat(), # Mock
                "period": f"{start_date.date()} to {end_date.date()}",
                "granularity": granularity,
                "marketplace": marketplace
            }
        )
        
    except Exception as e:
        # Log error
        print(f"Error in executive overview: {e}")
        # Re-raise HTTP exceptions
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

def _mock_fetch_data(start, end, marketplace):
    """Temporary mock to allow API testing without full DB integration yet"""
    return {
        'current_period': {'sales': 150000, 'spend': 50000, 'roas': 3.0, 'cvr': 0.12, 'cpc': 4.5},
        'previous_period': {'sales': 120000, 'spend': 45000, 'roas': 2.6, 'cvr': 0.10, 'cpc': 4.8},
        'medians': {'roas': 2.5, 'cvr': 0.10},
        'time_series': {
            'weekly': [
                {'date': '2024-01-01', 'sales': 20000, 'spend': 5000, 'roas': 4.0},
                {'date': '2024-01-08', 'sales': 25000, 'spend': 7000, 'roas': 3.5},
            ]
        },
        'decision_history': [
            {'type': 'bid_increase', 'measured_impact': 5000},
             {'type': 'pause', 'measured_impact': -1000}
        ],
        'quadrant_data': [],
        'revenue_by_match_type': {},
        'spend_distribution': {},
        'cost_efficiency_scatter': []
    }
