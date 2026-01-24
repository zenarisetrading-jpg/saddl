"use client";

import React from 'react';
import {
    ScatterChart,
    Scatter,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    ReferenceLine,
    Label
} from 'recharts';
import { PerformanceBreakdown } from '@/types/executive';

interface PerformanceOverviewProps {
    data: PerformanceBreakdown;
}

export function PerformanceOverview({ data }: PerformanceOverviewProps) {
    // Colors for zones
    const zoneColors = {
        scale: '#10b981', // Emerald
        optimize: '#3b82f6', // Blue
        watch: '#f59e0b', // Amber
        kill: '#ef4444', // Red
    };

    return (
        <div className="w-full bg-white p-6 rounded-2xl border border-slate-100 shadow-sm h-full">
            <div className="mb-6">
                <h3 className="text-lg font-semibold text-slate-900">Performance Matrix</h3>
                <p className="text-sm text-slate-500">ROAS vs CVR Distribution (Bubble size = Spend)</p>
            </div>

            <div className="h-[350px]">
                <ResponsiveContainer width="100%" height="100%">
                    <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                        <XAxis
                            type="number"
                            dataKey="x"
                            name="CVR"
                            unit="%"
                            tickFormatter={(val) => `${(val * 100).toFixed(0)}%`}
                            stroke="#94a3b8"
                            fontSize={12}
                        >
                            <Label value="Conversion Rate (CVR)" offset={-10} position="insideBottom" fill="#64748b" fontSize={12} />
                        </XAxis>
                        <YAxis
                            type="number"
                            dataKey="y"
                            name="ROAS"
                            stroke="#94a3b8"
                            fontSize={12}
                            domain={[0, 'auto']} // Start from 0
                        >
                            <Label value="ROAS" angle={-90} position="insideLeft" fill="#64748b" fontSize={12} />
                        </YAxis>
                        <Tooltip
                            cursor={{ strokeDasharray: '3 3' }}
                            content={({ active, payload }) => {
                                if (active && payload && payload.length) {
                                    const data = payload[0].payload;
                                    return (
                                        <div className="bg-white p-3 border border-slate-200 rounded-lg shadow-lg">
                                            <p className="font-semibold text-slate-900">{data.label}</p>
                                            <p className="text-sm text-slate-600">ROAS: {data.y.toFixed(2)}</p>
                                            <p className="text-sm text-slate-600">CVR: {(data.x * 100).toFixed(2)}%</p>
                                            <p className="text-xs text-slate-400 mt-1 uppercase">{data.zone}</p>
                                        </div>
                                    );
                                }
                                return null;
                            }}
                        />

                        {/* Median Lines (Mocked positions, ideally passed in props) */}
                        <ReferenceLine x={0.10} stroke="#cbd5e1" strokeDasharray="3 3" />
                        <ReferenceLine y={2.5} stroke="#cbd5e1" strokeDasharray="3 3" />

                        {/* Quadrant Labels */}
                        <ReferenceLine />

                        {/* Render points by zone to color them differently */}
                        {['scale', 'optimize', 'watch', 'kill'].map((zone) => (
                            <Scatter
                                key={zone}
                                name={zone}
                                data={data.quadrant_data.filter(d => d.zone === zone)}
                                fill={zoneColors[zone as keyof typeof zoneColors]}
                            />
                        ))}
                    </ScatterChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}
