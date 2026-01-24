"use client";

import React, { useEffect, useState, useCallback } from 'react';
import { ExecutiveDashboardData } from '@/types/executive';
import { KPICards } from './components/KPICards';
import { MomentumChart } from './components/MomentumChart';
import { DecisionImpactCard } from './components/DecisionImpact';
import { PerformanceOverview } from './components/PerformanceOverview';
import { RefreshCcw, AlertCircle } from 'lucide-react';

export default function ExecutiveDashboardPage() {
    const [data, setData] = useState<ExecutiveDashboardData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Date range state (default: last 30 days)
    const [dateRange] = useState({
        start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
        end: new Date()
    });
    const [granularity] = useState<'daily' | 'weekly' | 'monthly'>('weekly');
    const [marketplace] = useState('UAE Amazon');

    const fetchDashboardData = useCallback(async () => {
        setLoading(true);
        setError(null);

        try {
            const params = new URLSearchParams({
                start_date: dateRange.start.toISOString(),
                end_date: dateRange.end.toISOString(),
                granularity,
                marketplace
            });

            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
            const response = await fetch(`${apiUrl}/api/executive/overview?${params}`, {
                headers: {
                    'Content-Type': 'application/json',
                    // Add auth header if needed:
                    // 'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `API error: ${response.status}`);
            }

            const json = await response.json();
            setData(json);
        } catch (err) {
            console.error('Failed to load executive dashboard:', err);
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setLoading(false);
        }
    }, [dateRange, granularity, marketplace]);

    useEffect(() => {
        fetchDashboardData();
    }, [fetchDashboardData]);

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen bg-slate-50 text-slate-400">
                <RefreshCcw className="w-6 h-6 animate-spin mr-2" />
                Loading Dashboard...
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex flex-col items-center justify-center min-h-screen bg-slate-50 text-slate-600">
                <AlertCircle className="w-12 h-12 text-rose-500 mb-4" />
                <h2 className="text-xl font-semibold mb-2">Failed to Load Dashboard</h2>
                <p className="text-slate-500 mb-4">{error}</p>
                <button
                    onClick={() => fetchDashboardData()}
                    className="px-4 py-2 bg-slate-900 text-white rounded-lg text-sm font-medium hover:bg-slate-800 transition-colors"
                >
                    Retry
                </button>
            </div>
        );
    }

    if (!data) return null;

    return (
        <div className="min-h-screen bg-slate-50 p-8 font-sans text-slate-900">
            {/* Header */}
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-slate-900">Executive Overview</h1>
                    <p className="text-slate-500 mt-1">
                        Performance snapshot · {data.metadata.period} · {data.metadata.marketplace}
                    </p>
                </div>
                <div className="flex gap-3">
                    {/* Action buttons */}
                    <button
                        onClick={() => fetchDashboardData()}
                        className="px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium hover:bg-slate-50 transition-colors flex items-center gap-2"
                    >
                        <RefreshCcw className="w-4 h-4" />
                        Refresh
                    </button>
                    <button className="px-4 py-2 bg-slate-900 text-white rounded-lg text-sm font-medium hover:bg-slate-800 transition-colors shadow-sm">
                        Export Report
                    </button>
                </div>
            </div>

            {/* KPI Cards Row */}
            <div className="mb-6">
                <KPICards data={data.kpis} />
            </div>

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
                {/* Momentum Chart (Takes 2/3 width on large screens) */}
                <div className="lg:col-span-2">
                    <MomentumChart data={data.momentum} />
                </div>

                {/* Decision Impact (Takes 1/3 width) */}
                <div className="lg:col-span-1">
                    <DecisionImpactCard data={data.decision_impact} />
                </div>
            </div>

            {/* Bottom Section: Performance Overview */}
            <div className="grid grid-cols-1 gap-6">
                <PerformanceOverview data={data.performance} />
            </div>
        </div>
    );
}
