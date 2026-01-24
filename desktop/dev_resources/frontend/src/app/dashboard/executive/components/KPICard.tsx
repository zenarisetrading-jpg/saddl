import React from 'react';
import { KPIMetric } from '@/types/executive';
import { cn, formatCurrency, formatNumber, formatPercent } from '@/lib/utils';
import { ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';

interface KPICardProps {
    title: string;
    metric: KPIMetric;
    format?: 'currency' | 'number' | 'percent';
    className?: string;
}

export function KPICard({ title, metric, format = 'number', className }: KPICardProps) {
    const { value, delta_pct, delta_abs, trend } = metric;

    const isPositive = trend === 'up';
    const isNegative = trend === 'down';
    const isStable = trend === 'stable';

    // Color logic may vary by metric (e.g. Risk Index down is good), 
    // but standard logic is Green=Up, Red=Down. 
    // For Risk Index, the parent should inverse colors or we handle it via props.
    // For now assuming standard business metrics (Revenue, Profit).

    const trendColor = isPositive
        ? 'text-emerald-500'
        : isNegative
            ? 'text-rose-500'
            : 'text-slate-500';

    const TrendIcon = isPositive
        ? ArrowUpRight
        : isNegative
            ? ArrowDownRight
            : Minus;

    const formattedValue = format === 'currency'
        ? formatCurrency(value)
        : format === 'percent'
            ? formatPercent(value)
            : formatNumber(value);

    const formattedDelta = format === 'currency'
        ? formatCurrency(Math.abs(delta_abs))
        : format === 'percent'
            ? formatPercent(Math.abs(delta_abs))
            : formatNumber(Math.abs(delta_abs));

    return (
        <div className={cn("p-6 rounded-2xl bg-white border border-slate-100 shadow-sm hover:shadow-md transition-all", className)}>
            <div className="flex justify-between items-start mb-2">
                <h3 className="text-sm font-medium text-slate-500 uppercase tracking-wide">{title}</h3>
                {/* Sparkline placeholder - usually implemented with Recharts TinyChart */}
                {metric.sparkline && metric.sparkline.length > 0 && (
                    <div className="h-6 w-16 bg-slate-50 rounded opacity-50" />
                )}
            </div>

            <div className="flex items-baseline gap-2 mt-1">
                <span className="text-3xl font-bold text-slate-900 tracking-tight">{formattedValue}</span>
            </div>

            <div className={cn("flex items-center mt-3 text-sm font-medium", trendColor)}>
                <TrendIcon className="w-4 h-4 mr-1" />
                <span>{Math.abs(delta_pct).toFixed(1)}%</span>
                <span className="text-slate-400 ml-2 font-normal text-xs">
                    {delta_abs >= 0 ? '+' : '-'}{formattedDelta} vs prev
                </span>
            </div>
        </div>
    );
}
