import { Card, CardContent, Grid, Typography } from '@mui/material';
import * as React from 'react';
import CurrencyLabel from './currency-label';
import { PieChart, Pie, ResponsiveContainer, Tooltip } from 'recharts';
import { moneyColors } from './utils';

export function computeTotals(profile, yearly = false) {
    const mult = yearly ? 12 : 1;
    const budgetItems = profile?.budget || [];
    const out = {
        income: 0,
        expense: 0,
        net: 0,
    };
    for (const item of budgetItems) {
        let timePerMonth = 0;
        item.periods.forEach((period) => {
            const periodType = period.type.toLowerCase();
            if (periodType === 'monthly') {
                timePerMonth += 1;
            } else if (periodType === 'weekly') {
                timePerMonth += 4;
            } else if (periodType === 'daily') {
                timePerMonth += 30;
            } else if (periodType === 'yearly') {
                timePerMonth += 1 / 12;
            } else if (periodType === 'biweekly') {
                timePerMonth += 2;
            }
        });
        const amt = item.amount * timePerMonth * mult;
        out[item.type] += amt;
        out.net += item.type === 'income' ? amt : -amt;
    }
    return out;
}

export default function CalendarSummary({ sortedIncomeDates, profile }) {
    const [totals, setTotals] = React.useState({
        yearly: {
            income: 0,
            expense: 0,
            net: 0,
        },
        monthly: {
            income: 0,
            expense: 0,
            net: 0,
        },
    });
    const [budgetItemCount, setBudgetItemCount] = React.useState(0);
    const [budgetItemData, setBudgetItemData] = React.useState([]);

    React.useEffect(() => {
        setBudgetItemCount(profile?.budget?.length || 0);
        if (profile?.budget) {
            const bid = profile.budget.map((item) => ({
                name: item.name,
                value: parseFloat(item.amount.toString()),
                fill: item.type === 'income' ? moneyColors.dark.income : moneyColors.dark.expense,
                label: item.name,
            }));
            setBudgetItemData(bid);
        }
        setTotals({
            monthly: computeTotals(profile),
            yearly: computeTotals(profile, true),
        });
    }, [profile?.budget]);

    return (
        <div style={{ padding: '2px' }}>
            <h4>Summary</h4>
            <Grid container spacing={2}>
                <Grid size={3}>
                    <Card sx={{ padding: '8px', margin: '8px' }}>
                        <Typography
                            sx={{ fontSize: '24px', fontWeight: 'bold' }}
                        >
                            Accounts
                        </Typography>
                        <CardContent>
                            {profile.accounts.map((a) => (
                                <div key={a.id}>
                                    {a.name} ({a.type}) <Typography><CurrencyLabel amount={parseFloat(a.balance.toString())} /></Typography>
                                </div>
                            ))}
                        </CardContent>
                    </Card>
                </Grid>
                <Grid size={3}>
                    <Card sx={{ padding: '8px', margin: '8px' }}>
                        <Typography
                            sx={{ fontSize: '24px', fontWeight: 'bold' }}
                        >
                            Budget Items
                        </Typography>
                        <CardContent>
                            <ResponsiveContainer width={"100%"} minHeight={132}>
                                <PieChart width={400} height={400}>
                                    <Tooltip />
                                    <Pie data={budgetItemData} dataKey="value" cx="50%" cy="50%" outerRadius={60} fill="rgb(183, 28, 28)" label />
                                </PieChart>
                            </ResponsiveContainer>
                            {budgetItemCount} budget item(s)
                        </CardContent>
                    </Card>
                </Grid>
                <Grid size={3}>
                    <Card sx={{ padding: '8px', margin: '8px' }}>
                        <Typography
                            sx={{ fontSize: '24px', fontWeight: 'bold' }}
                        >
                            Monthly
                        </Typography>
                        <CardContent>
                            <ResponsiveContainer width={"100%"} minHeight={132}>
                                <PieChart width={400} height={400}>
                                    <Tooltip />
                                    <Pie data={[
                                        { name: 'income', value: totals.monthly.income, fill: moneyColors.dark.income },
                                        { name: 'expense', value: totals.monthly.expense, fill: moneyColors.dark.expense },
                                    ]} dataKey="value" cx="50%" cy="50%" outerRadius={60} fill="rgb(183, 28, 28)" label />
                                </PieChart>
                            </ResponsiveContainer>
                            <Typography>
                            <CurrencyLabel amount={totals.monthly.income} /> income
                            </Typography>
                            <Typography>
                            <CurrencyLabel amount={totals.monthly.expense} /> expense
                            </Typography>
                            <Typography><CurrencyLabel amount={totals.monthly.net} /> net</Typography>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid size={3}>
                    <Card sx={{ padding: '8px', margin: '8px' }}>
                        <Typography
                            sx={{ fontSize: '24px', fontWeight: 'bold' }}
                        >
                            Yearly
                        </Typography>
                        <CardContent>
                            <ResponsiveContainer width={"100%"} minHeight={132}>
                                <PieChart width={400} height={400}>
                                    <Tooltip />
                                    <Pie data={[
                                        { name: 'income', value: totals.yearly.income, fill: moneyColors.dark.income },
                                        { name: 'expense', value: totals.yearly.expense, fill: moneyColors.dark.expense },
                                    ]} dataKey="value" cx="50%" cy="50%" outerRadius={60} fill="rgb(183, 28, 28)" label />
                                </PieChart>
                            </ResponsiveContainer>
                            <Typography>
                                <CurrencyLabel amount={totals.yearly.income} /> income
                            </Typography>
                            <Typography>
                                <CurrencyLabel amount={totals.yearly.expense} /> expense
                            </Typography>
                            <Typography>
                                <CurrencyLabel amount={totals.yearly.net} /> net
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>
        </div>
    );
}
