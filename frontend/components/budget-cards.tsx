import { Card, CardContent, CardHeader } from '@mui/material';
import * as React from 'react';
import { useTheme } from '@mui/material/styles';
import { Label } from 'recharts';
import { useStore } from '../store';
import CurrencyLabel from './currency-label';
import DateLabel from './date-label';
import { GrowingPacker } from './utils';

const shadesOfRed = [
    '#661111',
    '#662211',
    '#663311',
    '#661122',
    '#661133',
    '#661144',
];

const shadesOfGreen = [
    '#116622',
];

const SCALE_CONST = 2500;
const MARGIN_CONST = 10;

export default function BudgetCards({ removeBudgetItem }) {
    const theme = useTheme();
    const budget = useStore((state) => (state as any).budget);
    const profile = useStore((state) => (state as any).profile);
    const [positioned, setPositioned] = React.useState([]);
    const [current, setCurrent] = React.useState(budget[0]);
    const [expensesOverlap, setExpensesOverlap] = React.useState(false);

    React.useEffect(() => {
        const packer = new GrowingPacker();
        let blocks = budget.filter((b) => {
            if (expensesOverlap) {
                return (b.type === 'expense');
            }
            return true;
        }).map((b) => ({
            ...b,
            width: Math.max(10, Math.sqrt(b.percentage * 100 * SCALE_CONST)) + MARGIN_CONST,
            height: Math.max(10, Math.sqrt(b.percentage * 100 * SCALE_CONST)) + MARGIN_CONST,
        }));
        packer.fit(blocks);
        if (expensesOverlap) {
            const incomeBlocks = budget.filter((b) => b.type === 'income').map((b) => ({
                ...b,
                width: Math.max(10, Math.sqrt(b.percentage * 100 * SCALE_CONST)) + MARGIN_CONST,
                height: Math.max(10, Math.sqrt(b.percentage * 100 * SCALE_CONST)) + MARGIN_CONST,
            }));
            for (const incomeBlock of incomeBlocks) {
                blocks.unshift({
                    ...incomeBlock,
                    x: 0,
                    y: 0,
                })
            }
        }
        setPositioned(blocks);
    }, []);

    return (
        <div>
            <div style={{
                display: 'flex',
                flexWrap: 'wrap',
                justifyContent: 'center',
                width: '1920px',
                height: '1080px',
            }}>
            {positioned ? positioned.map((row, i) => (
                <div key={(row as any).id} style={{
                    position: 'absolute',
                    left: `${(row as any).x + 20}px`,
                    top: `${(row as any).y + 300}px`,
                    backgroundColor: (row as any).type === 'expense' ? shadesOfRed[i % shadesOfRed.length] : shadesOfGreen[i % shadesOfGreen.length],
                    width: `${(row as any).width - MARGIN_CONST}px`,
                    height: `${(row as any).height - MARGIN_CONST}px`,
                }}
                onMouseEnter={() => setCurrent(row)}
                >
                    {(row as any).name}
                </div>
            )) : null}
            {current && <Card sx={{
                position: 'absolute',
                right: '20px',
                top: '300px',
                width: '300px',
                height: '400px',
            
            }}>
                <CardHeader sx={{
                    backgroundColor: (current as any).type === 'expense' 
                        ? (theme.palette.mode === 'dark' ? '#661111' : '#c62828')
                        : (theme.palette.mode === 'dark' ? '#116622' : '#2e7d32'),
                    color: 'white',
                }}></CardHeader>
                <CardContent>
                    <h4>{(current as any).name}</h4>
                    <div>{(current as any).type} - {(current as any)?.group?.name || 'No Group'}</div>
                    <div>{((current as any).percentage * 100.0).toFixed(2)}%</div>
                    <div>
                        Amount
                        <CurrencyLabel amount={(current as any).amount} /></div>
                    <div>
                        Monthly
                        {CurrencyLabel({amount: (current as any).monthlyAmount || 0})}
                    </div>
                    <div>
                        Yearly
                        {CurrencyLabel({amount: (current as any).yearlyAmount || 0})}
                    </div>
                    {(current as any).periods.map((p, pi) => (
                        <div key={`${pi}-${p.type}`}>
                            {p.type}-{p.value}
                            {p.businessDay !== 'none'
                                ? ` (${p.businessDay})`
                                : ''}
                        </div>
                    ))}
                    <div>
                        Updated
                        <DateLabel date={(current as any).updatedAt} />
                    </div>
                    <div>
                        Start
                        <DateLabel date={(current as any).startDate} />
                    </div>
                    <div>
                        End
                        <DateLabel date={(current as any).endDate} />
                    </div>
                </CardContent>
            </Card>}
            </div>
        </div>
    );
}
