/**
 * Executive Dashboard Data Types
 * Matches backend/models/executive_schemas.py
 */

export type TrendDirection = 'up' | 'down' | 'stable';
export type MomentumClassification = 'scale_push' | 'efficiency_correction' | 'risk_zone' | 'healthy_scale' | 'stable';
export type DecisionType = 'promote' | 'prevent' | 'protect';
export type QuadrantZone = 'scale' | 'optimize' | 'watch' | 'kill';

export interface KPIMetric {
    value: number;
    delta_pct: number;
    delta_abs: number;
    trend: TrendDirection;
    sparkline: number[];
}

export interface KPIs {
    revenue: KPIMetric;
    net_contribution: KPIMetric;
    efficiency_score: KPIMetric;
    risk_index: KPIMetric;
    scale_headroom: KPIMetric;
}

export interface MomentumDataPoint {
    date: string; // ISO date
    revenue: number;
    spend_allocation: Record<string, number>; // { [classification]: amount }
    efficiency_line: number; // % vs baseline
}

export interface DecisionCategory {
    count: number;
    impact: number;
    type: DecisionType;
    detail: string;
}

export interface DecisionImpact {
    period: string;
    net_impact: number;
    net_impact_pct: number;
    bid_ups: DecisionCategory;
    bid_downs: DecisionCategory;
    pauses: DecisionCategory;
    negatives: DecisionCategory;
}

export interface QuadrantPoint {
    x: number; // CVR
    y: number; // ROAS
    size: number; // Orders/Spend
    label: string;
    zone: QuadrantZone;
}

export interface PerformanceBreakdown {
    quadrant_data: QuadrantPoint[];
    revenue_by_match_type: Record<string, number>;
    spend_distribution: Record<string, number>;
    cost_efficiency_scatter: Array<{ x: number; y: number; z: number }>; // Simplified
}

export interface ExecutiveDashboardData {
    kpis: KPIs;
    momentum: MomentumDataPoint[];
    decision_impact: DecisionImpact;
    performance: PerformanceBreakdown;
    metadata: {
        data_freshness: string;
        period: string;
        granularity: string;
        marketplace: string;
    };
}
