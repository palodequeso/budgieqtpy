import * as React from 'react';
import { PieChart, Pie, ResponsiveContainer, Tooltip } from 'recharts';
import { moneyColors } from './utils';
import { useStore } from '../store';

export default function BudgetChart() {
    const [chartData, setChartData] = React.useState([]);

    const budget = useStore((state) => (state as any).budget);

    React.useEffect(() => {
        const bid = budget
        .filter((item) => item.type === 'expense')
        .map((item) => ({
            name: item.name,
            value: parseFloat(item.amount.toString()),
            fill: item.type === 'income' ? moneyColors.dark.income : moneyColors.dark.expense,
            label: item.name,
        }));
        setChartData(bid);
    }, [budget]);

    return (
        <div>
            {chartData && (
                <ResponsiveContainer width={"100%"} minHeight={1000}>
                    <PieChart width={800} height={800}>
                        <Tooltip />
                        <Pie
                            data={chartData}
                            dataKey="value"
                            cx="50%"
                            cy="50%"
                            outerRadius={400}
                            fill="rgb(183, 28, 28)"
                            label
                        />
                    </PieChart>
                </ResponsiveContainer>
            )}
        </div>
    );
}
