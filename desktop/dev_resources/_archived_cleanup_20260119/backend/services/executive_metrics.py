"""
Executive Metrics Service
PURE TRANSFORMATION LOGIC - No database calls, no API calls
Input: Existing cached data (dict)
Output: Derived metrics (dict)
"""

import numpy as np
from typing import Dict, List, Any
from datetime import datetime, timedelta

class ExecutiveMetricsService:
    """
    Transforms existing metrics into executive-level insights.
    ALL methods are pure functions (no side effects).
    """
    
    def compute_kpis(self, data: Dict[str, Any]) -> Dict:
        """
        Compute top-line KPIs from existing metrics.
        
        Args:
            data: {
                'current_period': {'sales': float, 'spend': float, 'roas': float, ...},
                'previous_period': {...},
                'medians': {'roas': float, 'cvr': float}
            }
        
        Returns:
            Dict matching KPIs schema
        """
        current = data.get('current_period', {})
        previous = data.get('previous_period', {})
        medians = data.get('medians', {})
        
        # Revenue
        revenue = self._compute_metric(
            current.get('sales', 0), 
            previous.get('sales', 0)
        )
        
        # Net Contribution = Revenue - Spend
        current_contrib = current.get('sales', 0) - current.get('spend', 0)
        prev_contrib = previous.get('sales', 0) - previous.get('spend', 0)
        
        net_contribution = self._compute_metric(
            current_contrib,
            prev_contrib
        )
        
        # Efficiency Score (composite: 50% ROAS + 30% CVR + 20% CPC trend)
        efficiency_score = self._compute_efficiency_score(
            current, 
            previous, 
            medians
        )
        
        # Risk Index (% spend in low-performance zone)
        risk_index = self._compute_risk_index(
            data.get('campaign_performance', [])
        )
        
        # Scale Headroom (% spend in high-performance zone)
        scale_headroom = self._compute_scale_headroom(
            data.get('campaign_performance', [])
        )
        
        return {
            "revenue": revenue,
            "net_contribution": net_contribution,
            "efficiency_score": efficiency_score,
            "risk_index": risk_index,
            "scale_headroom": scale_headroom
        }
    
    def _compute_metric(self, current_value: float, previous_value: float) -> Dict:
        """Helper: compute metric with delta and trend"""
        delta_abs = current_value - previous_value
        delta_pct = (delta_abs / previous_value * 100) if previous_value != 0 else 0
        
        # Trend classification
        if delta_pct > 2:
            trend = "up"
        elif delta_pct < -2:
            trend = "down"
        else:
            trend = "stable"
        
        return {
            "value": current_value,
            "delta_abs": delta_abs,
            "delta_pct": delta_pct,
            "trend": trend,
            "sparkline": []  # Populated separately if needed
        }
    
    def _compute_efficiency_score(
        self, 
        current: Dict, 
        previous: Dict, 
        medians: Dict
    ) -> Dict:
        """
        Composite efficiency score (0-100):
        - 50% weight: ROAS vs median
        - 30% weight: CVR vs median
        - 20% weight: CPC trend (lower is better)
        """
        median_roas = medians.get('roas', 2.5) or 2.5
        median_cvr = medians.get('cvr', 0.10) or 0.10
        
        # ROAS component (0-50 points)
        current_roas = current.get('roas', 0)
        roas_ratio = current_roas / median_roas if median_roas > 0 else 0
        roas_score = min(50, roas_ratio * 50)
        
        # CVR component (0-30 points)
        current_cvr = current.get('cvr', 0)
        cvr_ratio = current_cvr / median_cvr if median_cvr > 0 else 0
        cvr_score = min(30, cvr_ratio * 30)
        
        # CPC component (0-20 points)
        # Award 20 points if CPC decreased, 10 if stable
        current_cpc = current.get('cpc', 0)
        prev_cpc = previous.get('cpc', 0)
        
        cpc_delta = (current_cpc - prev_cpc) / prev_cpc if prev_cpc > 0 else 0
        
        if cpc_delta <= -0.05:  # 5%+ decrease
            cpc_score = 20
        elif cpc_delta <= 0.05:  # Stable
            cpc_score = 15
        else:  # Increased
            cpc_score = 10
        
        total = roas_score + cvr_score + cpc_score
        
        # Compare to previous efficiency score (if exists)
        previous_efficiency = previous.get('efficiency_score', total)
        
        return self._compute_metric(total, previous_efficiency)
    
    def _compute_risk_index(self, campaigns: List[Dict]) -> Dict:
        """
        Risk Index = % of spend in low-performance quadrant
        Low performance = ROAS < median AND CVR < median
        """
        if not campaigns:
            return self._compute_metric(0, 0)
        
        total_spend = sum(c.get('spend', 0) for c in campaigns)
        if total_spend == 0:
            return self._compute_metric(0, 0)
        
        # Calculate medians
        roas_values = [c.get('roas', 0) for c in campaigns]
        cvr_values = [c.get('cvr', 0) for c in campaigns]
        
        if not roas_values or not cvr_values:
             return self._compute_metric(0, 0)

        median_roas = np.median(roas_values)
        median_cvr = np.median(cvr_values)
        
        # Sum spend in risky zone
        risky_spend = sum(
            c.get('spend', 0) for c in campaigns
            if c.get('roas', 0) < median_roas and c.get('cvr', 0) < median_cvr
        )
        
        risk_pct = risky_spend / total_spend
        
        # For trend, we'd need previous period data (not shown here)
        return self._compute_metric(risk_pct, risk_pct)  # Simplified
    
    def _compute_scale_headroom(self, campaigns: List[Dict]) -> Dict:
        """
        Scale Headroom = % of spend in high-performance quadrant
        High performance = ROAS > median AND CVR > median
        """
        if not campaigns:
            return self._compute_metric(0, 0)
        
        total_spend = sum(c.get('spend', 0) for c in campaigns)
        if total_spend == 0:
            return self._compute_metric(0, 0)
        
        # Calculate medians
        roas_values = [c.get('roas', 0) for c in campaigns]
        cvr_values = [c.get('cvr', 0) for c in campaigns]

        if not roas_values or not cvr_values:
             return self._compute_metric(0, 0)

        median_roas = np.median(roas_values)
        median_cvr = np.median(cvr_values)
        
        scale_spend = sum(
            c.get('spend', 0) for c in campaigns
            if c.get('roas', 0) > median_roas and c.get('cvr', 0) > median_cvr
        )
        
        scale_pct = scale_spend / total_spend
        
        return self._compute_metric(scale_pct, scale_pct)
    
    def compute_momentum(
        self, 
        data: Dict, 
        granularity: str = "weekly"
    ) -> List[Dict]:
        """
        Classify momentum for each time period.
        
        CORRECTED MOMENTUM LOGIC:
        - Revenue ↑ AND Efficiency >= Median AND ΔEfficiency ↓ → "scale_push"
        - Revenue ↓ AND Efficiency >= Median AND ΔEfficiency ↑ → "efficiency_correction"
        - Revenue ↓ AND Efficiency < Median → "risk_zone"
        - Revenue ↑ AND Efficiency > Median → "healthy_scale"
        - Else → "stable"
        """
        periods = data.get('time_series', {}).get(granularity, [])
        medians = data.get('medians', {})
        
        results = []
        
        for i, period in enumerate(periods):
            if i == 0:
                # First period has no comparison
                classification = "stable"
                spend_allocation = {classification: period.get('spend', 0)}
            else:
                prev = periods[i-1]
                classification = self._classify_momentum(period, prev, medians)
                spend_allocation = {classification: period.get('spend', 0)}
            
            # Ensure safe division
            roas = period.get('roas', 0)
            median_roas = medians.get('roas', 1) or 1
            
            results.append({
                "date": period['date'],
                "revenue": period.get('sales', 0),
                "spend_allocation": spend_allocation,
                "efficiency_line": (roas / median_roas) * 100
            })
        
        return results
    
    def _classify_momentum(
        self, 
        current: Dict, 
        previous: Dict, 
        medians: Dict
    ) -> str:
        """
        Apply EXACT momentum classification logic from spec.
        """
        # Calculate deltas
        prev_sales = previous.get('sales', 0)
        delta_revenue = (
            (current.get('sales', 0) - prev_sales) / prev_sales
            if prev_sales != 0 else 0
        )
        
        prev_roas = previous.get('roas', 0)
        delta_efficiency = (
            (current.get('roas', 0) - prev_roas) / prev_roas
            if prev_roas != 0 else 0
        )
        
        # Efficiency vs median
        median_roas = medians.get('roas', 1) or 1
        efficiency_vs_median = current.get('roas', 0) / median_roas
        
        # Apply classification rules
        if delta_revenue > 0 and efficiency_vs_median >= 1.0 and delta_efficiency < 0:
            return "scale_push"
        elif delta_revenue < 0 and efficiency_vs_median >= 1.0 and delta_efficiency > 0:
            return "efficiency_correction"
        elif delta_revenue < 0 and efficiency_vs_median < 1.0:
            return "risk_zone"
        elif delta_revenue > 0 and efficiency_vs_median > 1.0:
            return "healthy_scale"
        else:
            return "stable"
    
    def compute_decision_impact(self, data: Dict) -> Dict:
        """
        Aggregate impact of decisions from existing decision history.
        This is POST-HOC analysis only (read-only).
        """
        decisions = data.get('decision_history', [])
        
        bid_ups = self._aggregate_decisions(decisions, 'bid_increase')
        bid_downs = self._aggregate_decisions(decisions, 'bid_decrease')
        pauses = self._aggregate_decisions(decisions, 'pause')
        negatives = self._aggregate_decisions(decisions, 'negative')
        
        net_impact = sum([
            bid_ups['impact'],
            bid_downs['impact'],
            pauses['impact'],
            negatives['impact']
        ])
        
        total_revenue = data.get('current_period', {}).get('sales', 0) # Fixed to default 0
        if total_revenue == 0:
            # Fallback to avoid div by zero, or use 1 if strictly needed but 0 is safer for pct
            total_revenue = 1 if total_revenue == 0 else total_revenue
            
        net_impact_pct = (net_impact / total_revenue * 100) if total_revenue != 0 else 0
        
        return {
            "period": "Last 14 Days",
            "net_impact": net_impact,
            "net_impact_pct": net_impact_pct,
            "bid_ups": bid_ups,
            "bid_downs": bid_downs,
            "pauses": pauses,
            "negatives": negatives
        }
    
    def _aggregate_decisions(
        self, 
        decisions: List[Dict], 
        decision_type: str
    ) -> Dict:
        """Sum impact of all decisions of a given type"""
        filtered = [d for d in decisions if d.get('type') == decision_type]
        
        total_impact = sum(d.get('measured_impact', 0) for d in filtered)
        
        # Categorize decision type
        if decision_type == 'bid_increase':
            category_type = "promote"
            detail = "Positions - Presence"
        elif decision_type == 'bid_decrease':
            category_type = "prevent"
            detail = "Preventing waste"
        elif decision_type == 'pause':
            category_type = "prevent"
            detail = "Pacsternine - Waste"
        else:  # negative
            category_type = "prevent"
            detail = "Presennin - Unses"
        
        return {
            "count": len(filtered),
            "impact": total_impact,
            "type": category_type,
            "detail": detail
        }
