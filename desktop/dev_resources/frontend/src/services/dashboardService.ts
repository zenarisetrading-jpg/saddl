import { ExecutiveDashboardData } from '@/types/executive';

export const MOCK_DASHBOARD_DATA: ExecutiveDashboardData = {
    kpis: {
        revenue: {
            value: 245000,
            delta_pct: 12.5,
            delta_abs: 27000,
            trend: 'up',
            sparkline: [210000, 215000, 220000, 225000, 235000, 245000]
        },
        net_contribution: {
            value: 85000,
            delta_pct: 8.2,
            delta_abs: 6400,
            trend: 'up',
            sparkline: [75000, 78000, 80000, 82000, 84000, 85000]
        },
        efficiency_score: {
            value: 88,
            delta_pct: 2.3,
            delta_abs: 2,
            trend: 'up',
            sparkline: []
        },
        risk_index: {
            value: 0.12,
            delta_pct: -5.0,
            delta_abs: -0.01,
            trend: 'down', // Down is good for risk
            sparkline: []
        },
        scale_headroom: {
            value: 0.45,
            delta_pct: 10.0,
            delta_abs: 0.04,
            trend: 'up',
            sparkline: []
        }
    },
    momentum: [
        { date: '2024-01-01', revenue: 30000, spend_allocation: { scale_push: 2000, stable: 8000 }, efficiency_line: 110 },
        { date: '2024-01-08', revenue: 32000, spend_allocation: { scale_push: 3000, stable: 8000 }, efficiency_line: 112 },
        { date: '2024-01-15', revenue: 35000, spend_allocation: { scale_push: 4000, stable: 8500 }, efficiency_line: 108 },
        { date: '2024-01-22', revenue: 34000, spend_allocation: { efficiency_correction: 2000, stable: 9000 }, efficiency_line: 105 },
        { date: '2024-01-29', revenue: 38000, spend_allocation: { healthy_scale: 5000, stable: 9000 }, efficiency_line: 115 },
    ],
    decision_impact: {
        period: 'Last 14 Days',
        net_impact: 12500,
        net_impact_pct: 5.1,
        bid_ups: { count: 12, impact: 8500, type: 'promote', detail: 'Positions - Presence' },
        bid_downs: { count: 8, impact: -2000, type: 'prevent', detail: 'Preventing waste' },
        pauses: { count: 4, impact: -1500, type: 'prevent', detail: 'Pacsternine - Waste' },
        negatives: { count: 15, impact: 7500, type: 'prevent', detail: 'Presennin - Unses' },
    },
    performance: {
        quadrant_data: [
            { x: 0.15, y: 3.5, size: 5000, label: 'Hero 1', zone: 'scale' },
            { x: 0.05, y: 1.2, size: 2000, label: 'Dog 1', zone: 'kill' },
            { x: 0.12, y: 2.8, size: 3000, label: 'Core 1', zone: 'optimize' },
        ],
        revenue_by_match_type: { 'EXACT': 150000, 'PHRASE': 60000, 'BROAD': 35000 },
        spend_distribution: { 'EXACT': 0.6, 'PHRASE': 0.25, 'BROAD': 0.15 },
        cost_efficiency_scatter: []
    },
    metadata: {
        data_freshness: new Date().toISOString(),
        period: '2024-01-01 to 2024-01-30',
        granularity: 'weekly',
        marketplace: 'UAE Amazon'
    }
};

export async function fetchDashboardData(): Promise<ExecutiveDashboardData> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500));
    return MOCK_DASHBOARD_DATA;
}
