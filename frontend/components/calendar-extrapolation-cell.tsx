import * as React from 'react';
import CurrencyLabel from './currency-label';
import { CalendarEntry } from './calendar-extrapolation';
import { TableCell } from '@mui/material';
import { monthColors } from './utils';

export default function CalendarExtrapolationCell({ entry, date, theme, schedule, setEditingCell }: { entry: CalendarEntry, date: string, theme: any, schedule: any, setEditingCell: any }) {
    const paid = entry.items && entry.items.length > 0 ? entry.items.reduce((acc, item) => {
        return acc && item.ledgerEntry && item.ledgerEntry.id !== null;
    }, true) : false;
    return (
        <TableCell
            key={date + '-tc'}
            className={`currency calendar-entry-month-${date.substring(5, 7)}`}
            style={{ backgroundColor: monthColors[theme][parseInt(date.substring(5, 7), 10) - 1] }}
            onClick={() => setEditingCell(entry)}
        >
            <span className={['currency-amount', paid ? 'currency-paid' : ''].join( ' ')} >
                {entry.amount !== 0 ? <CurrencyLabel amount={entry.amount} /> : ''}
            </span>
        </TableCell>
    );
}
