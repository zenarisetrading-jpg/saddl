import React from 'react';
import { KPIs } from '@/types/executive';
import { KPICard } from './KPICard';

interface KPICardsProps {
    data: KPIs;
}

export function KPICards({ data }: KPICardsProps) {
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            <KPICard
                title="Revenue"
                metric={data.revenue}
                format="currency"
            />
            <KPICard
                title="Net Contribution"
                metric={data.net_contribution}
                format="currency"
            />
            <KPICard
                title="Efficiency Score"
                metric={data.efficiency_score}
                format="number"
            />
            <KPICard
                title="Risk Index"
                metric={data.risk_index}
                format="percent"
                className="border-rose-100 bg-rose-50/30" // Subtle styling for risk
            />
            <KPICard
                title="Scale Headroom"
                metric={data.scale_headroom}
                format="percent"
                className="border-emerald-100 bg-emerald-50/30" // Subtle styling for opportunity
            />
        </div>
    );
}
