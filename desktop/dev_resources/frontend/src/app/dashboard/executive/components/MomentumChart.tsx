"use client";

import React from 'react';
import {
    ComposedChart,
    Bar,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    ReferenceLine
} from 'recharts';
import { MomentumDataPoint } from '@/types/executive';
import { formatCurrency, formatNumber } from '@/lib/utils';

interface MomentumChartProps {
    data: MomentumDataPoint[];
}

export function MomentumChart({ data }: MomentumChartProps) {
    // Transform data for Recharts (flatten spend_allocation for stacked bars)
    const chartData = data.map(d => ({
        ...d,
        ...d.spend_allocation, // Flattens { scale_push: 100 } to { scale_push: 100 } at root
    }));

    // Keys for stacked bars
    const stackKeys = ['scale_push', 'healthy_scale', 'efficiency_correction', 'risk_zone', 'stable'];

    const colors: Record<string, string> = {
        scale_push: '#10b981', // Emerald 500
        healthy_scale: '#3b82f6', // Blue 500
        efficiency_correction: '#f59e0b', // Amber 500
        risk_zone: '#ef4444', // Red 500
        stable: '#94a3b8', // Slate 400
    };

    const labels: Record<string, string> = {
        scale_push: 'Scale Push',
        healthy_scale: 'Healthy Scale',
        efficiency_correction: 'Efficiency Correction',
        risk_zone: 'Risk Zone',
        stable: 'Stable',
    };

    return (
        <div className="w-full h-[400px] bg-white p-6 rounded-2xl border border-slate-100 shadow-sm">
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h3 className="text-lg font-semibold text-slate-900">Momentum & Efficiency</h3>
                    <p className="text-sm text-slate-500">Revenue trend vs Efficiency Baseline</p>
                </div>
                <div className="flex gap-2">
                    {/* Legend or interactions could go here */}
                </div>
            </div>

            <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={chartData} margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                    <XAxis
                        dataKey="date"
                        tickFormatter={(value) => new Date(value).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                        stroke="#94a3b8"
                        fontSize={12}
                        tickLine={false}
                        axisLine={false}
                    />
                    <YAxis
                        yAxisId="left"
                        tickFormatter={(value) => formatNumber(value)}
                        stroke="#94a3b8"
                        fontSize={12}
                        tickLine={false}
                        axisLine={false}
                    />
                    <YAxis
                        yAxisId="right"
                        orientation="right"
                        tickFormatter={(value) => `${value}%`}
                        domain={[50, 150]} // Focus on deviation around 100%
                        stroke="#6366f1"
                        fontSize={12}
                        tickLine={false}
                        axisLine={false}
                    />
                    <Tooltip
                        formatter={(value: any, name: any) => {
                            if (typeof value !== 'number') return [value, name];
                            if (name === 'efficiency_line') return [`${value.toFixed(1)}%`, 'Efficiency vs Baseline'];
                            return [formatCurrency(value), labels[name] || name];
                        }}
                        contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                    />
                    <Legend formatter={(value) => labels[value] || (value === 'efficiency_line' ? 'Efficiency vs Baseline' : value)} />

                    <ReferenceLine y={100} yAxisId="right" stroke="#6366f1" strokeDasharray="3 3" opacity={0.5} />

                    {/* Stacked Bars for Spend/Revenue Contribution */}
                    {stackKeys.map(key => (
                        <Bar
                            key={key}
                            dataKey={key}
                            stackId="a"
                            fill={colors[key]}
                            yAxisId="left"
                            radius={[4, 4, 0, 0]} // Only top radius on top bar effectively, but simple setup here
                        />
                    ))}

                    {/* Efficiency Line */}
                    <Line
                        type="monotone"
                        dataKey="efficiency_line"
                        stroke="#6366f1"
                        strokeWidth={3}
                        dot={{ r: 4, fill: '#6366f1', strokeWidth: 2, stroke: '#fff' }}
                        yAxisId="right"
                    />
                </ComposedChart>
            </ResponsiveContainer>
        </div>
    );
}
