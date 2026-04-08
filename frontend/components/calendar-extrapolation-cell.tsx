import * as React from 'react';
import CurrencyLabel from './currency-label';
import { CalendarEntry } from './calendar-extrapolation';
import { TableCell } from '@mui/material';
import { monthColors } from './utils';

const overdueColors = {
    dark: '#4a1a1a',
    light: '#ffcdd2',
};

export default function CalendarExtrapolationCell({ entry, date, incomeDate, theme, schedule, setEditingCell, onDrop, onQuickPay }: {
    entry: any,
    date: string,
    incomeDate: string,
    theme: any,
    schedule: any,
    setEditingCell: any,
    onDrop?: (e: React.DragEvent) => void,
    onQuickPay?: (entry: any) => void,
}) {
    const [dragOver, setDragOver] = React.useState(false);
    const paid = entry.items && entry.items.length > 0 ? entry.items.reduce((acc, item) => {
        return acc && item.ledger_entry && item.ledger_entry.id !== null;
    }, true) : false;

    const today = new Date().toISOString().slice(0, 10);
    const isOverdue = incomeDate < today && !paid;

    const bgColor = isOverdue
        ? overdueColors[theme] || overdueColors.dark
        : monthColors[theme][parseInt(date.substring(5, 7), 10) - 1];

    const handleDoubleClick = () => {
        if (!onQuickPay) return;
        const unpaidItems = (entry.items || []).filter(
            (item: any) => !(item.ledger_entry && item.ledger_entry.id !== null)
        );
        if (unpaidItems.length === 1) {
            onQuickPay(entry);
        } else {
            // Multiple unpaid items or none — open the detail dialog
            setEditingCell(entry);
        }
    };

    return (
        <TableCell
            key={date + '-tc'}
            className={`currency calendar-entry-month-${date.substring(5, 7)}`}
            style={{
                backgroundColor: bgColor,
                whiteSpace: 'nowrap',
                minWidth: '100px',
                cursor: 'grab',
                opacity: dragOver ? 0.6 : 1,
                outline: dragOver ? '2px dashed #1976d2' : 'none',
            }}
            draggable={true}
            onDragStart={(e) => {
                e.dataTransfer.setData('application/json', JSON.stringify({
                    budget_item_id: entry.budget_item.id,
                    from_income_date: incomeDate,
                }));
                e.dataTransfer.effectAllowed = 'move';
            }}
            onDragOver={(e) => {
                e.preventDefault();
                e.dataTransfer.dropEffect = 'move';
            }}
            onDragEnter={(e) => {
                e.preventDefault();
                setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => {
                e.preventDefault();
                setDragOver(false);
                if (onDrop) onDrop(e);
            }}
            onClick={() => setEditingCell(entry)}
            onDoubleClick={(e) => {
                e.stopPropagation();
                handleDoubleClick();
            }}
        >
            <span className={['currency-amount', paid ? 'currency-paid' : ''].join(' ')}>
                {entry.amount !== 0 ? <CurrencyLabel amount={entry.items.reduce((acc0, item) => acc0 + item.extrapolation_item.amount, 0)} /> : ''}
            </span>
        </TableCell>
    );
}
