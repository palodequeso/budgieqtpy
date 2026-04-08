import {
    Button,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    TableBody,
    TableCell,
    TableRow,
    Typography,
} from '@mui/material';
import * as React from 'react';
import CalendarExtrapolationCell from './calendar-extrapolation-cell';
import { monthColors } from './utils';
import CurrencyLabel from './currency-label';
import { api } from './renderUtils';
import { useStore } from '../store';
import * as moment from 'moment';

export class CalendarEntry {
    public incomeDate: string;
    public income_date: string; // API uses snake_case
    public budgetItem: any;
    public budget_item: any; // API uses snake_case
    public items: any[]; // extrapolation items, ledger entries, etc?
    public get amount(): number {
        return this.items.reduce((acc, item) => {
            const itemAmount = item.extrapolation_item?.amount ?? item.amount ?? 0;
            return parseFloat(acc.toString()) + parseFloat(itemAmount.toString());
        }, 0.0);
    }
};

export class CalendarIncomeColumn {
    public incomeDate: string;
    public date: string;
    public entries: CalendarEntry[];
    public carry: number; // leftover from previous column
    public income: any;

    constructor(incomeDate: string) {
        let date = incomeDate;
        if (typeof incomeDate === 'object' || incomeDate.length > 10) {
            date = moment(incomeDate).format('YYYY-MM-DD');
        }

        this.incomeDate = date;
        this.date = date;
        this.entries = [];
        this.carry = 0;
        this.income = null;
    }

    static fromData(date: string, entries: CalendarEntry[], carry: number, income: any) {
        const column = new CalendarIncomeColumn(date);
        column.entries = entries;
        column.carry = carry;
        column.income = income;
        return column;
    }

    public get subTotal(): number {
        return this.entries.reduce((amount, entry) => {
            // guard against string numbers :(
            return parseFloat(amount.toString()) + parseFloat(entry.amount.toString());
        }, 0) + parseFloat(this.income.amount);
    }

    public get total(): number {
        return this.carry + this.subTotal;
    }
}

export class CalendarExtrapolationGrid {
    public sortedIncomeDates: string[] = [];
    public sortedBudgetItems: any[] = [];
    public columns: CalendarIncomeColumn[] = [];
    public grid: Array<Array<CalendarEntry | null>> = [];

    constructor(sortedIncomeDate, columns) {
        this.sortedIncomeDates = sortedIncomeDate;
        this.columns = columns;
        this.buildBudgetItems();
        this.initializeGrid();
    }

    public buildBudgetItems() {
        // const uniqueBudgetItems = {};
        // for (const column of this.columns) {
        //     for (const entry of column.entries) {
        //         if (!entry.budgetItem) {
        //             continue;
        //         }

        //         if (!uniqueBudgetItems[entry.budgetItem.id]) {
        //             uniqueBudgetItems[entry.budgetItem.id] = entry.budgetItem;
        //         }
        //     }
        // }
        // this.sortedBudgetItems = Object.keys(uniqueBudgetItems).map((id) => uniqueBudgetItems[id]).sort((a, b) => b.amount - a.amount);
    }

    public initializeGrid() {
        this.grid = [];
        // for (const budgetItem of this.sortedBudgetItems) {
        //     const row: Array<CalendarEntry | null> = [];
        //     for (const incomeDate of this.sortedIncomeDates) {
        //         const column = this.columns.find((c) => c.incomeDate.startsWith(incomeDate));
        //         if (!column) {
        //             continue;
        //         }

        //         const foundColumnEntry = column.entries.find((e) => e.budgetItem && e.budgetItem.id === budgetItem.id);
        //         if (foundColumnEntry) {
        //             // row.push(foundColumnEntry.entries.find((e) => e.budgetItem.id === budgetItem.id));
        //             row.push(foundColumnEntry);
        //         } else {
        //             row.push(null);
        //         }
        //     }
        //     this.grid.push(row);
        // }

        // for (const incomeDate of this.sortedIncomeDates) {
        //     const row: Array<CalendarEntry | null> = [];
            // const column = this.columns.find((c) => c.incomeDate.startsWith(incomeDate));
            // if (!column) {
            //     continue;
            // }

            // for (const entry of column.entries) {
            //     if (entry.budgetItem) {
            //         continue;
            //     }

            //     // handle one off expense that is planned
            //     row.push(entry);
            // }
            // this.grid.push(row);
        // }
    }
}

function getMonthByColumnIndex(index: number, sortedIncomeDates: string[]) {
    return parseInt(sortedIncomeDates[index].substring(5, 7), 10);
}

function columnTotal(column) {
    if (!column) {
        return 0;
    }
    let total = column.starting_balance;
    total += column.incomes.reduce((acc0: any, income: any) => acc0 + income.items.reduce((acc1: any, item: any) => acc1 + item.extrapolation_item.amount, 0), 0);
    total += column.expenses.reduce((acc0: any, expense: any) => acc0 + expense.items.reduce((acc1: any, item: any) => acc1 + item.extrapolation_item.amount, 0), 0);
    return total;
}

function columnSafeToSpend(column) {
    if (!column) return 0;
    let safe = column.incomes.reduce((acc0: any, income: any) => acc0 + income.items.reduce((acc1: any, item: any) => acc1 + item.extrapolation_item.amount, 0), 0);
    safe += column.expenses.reduce((acc0: any, expense: any) => acc0 + expense.items.reduce((acc1: any, item: any) => acc1 + item.extrapolation_item.amount, 0), 0);
    return safe;
}

export default function CalendarExtrapolation({
    // extrapolation,
    schedule,
    setEditingCell,
    theme,
    miscRowCount,
    miscEntries,
    onReload,
}: {
    // extrapolation: { [s: string]: CalendarIncomeColumn },
    schedule: any,
    setEditingCell: (cell: any) => void,
    theme: string,
    miscRowCount: number,
    miscEntries: any,
    onReload: () => void,
}) {
    const profile = useStore((state) => (state as any).profile);
    const [dragOverCell, setDragOverCell] = React.useState<string | null>(null);
    const [pendingMove, setPendingMove] = React.useState<any>(null);

    // Quick pay handler: mark a single unpaid item as paid using the first account
    const handleQuickPay = async (entry: any) => {
        if (!profile) return;
        const unpaidItems = (entry.items || []).filter(
            (item: any) => !(item.ledger_entry && item.ledger_entry.id !== null)
        );
        if (unpaidItems.length !== 1) return;
        const item = unpaidItems[0];
        const accountId = profile.accounts?.[0]?.id;
        if (!accountId) {
            alert('No account available for quick pay. Please add an account first.');
            return;
        }
        try {
            await api.post(`/budget/markpaid/${profile.id}`, {
                extrapolationItemId: item.extrapolation_item?.id ?? item.id,
                accountId: accountId,
            });
            onReload();
        } catch (err) {
            alert(`Quick pay failed: ${err.message}`);
        }
    };

    const handleDrop = (e: React.DragEvent, targetDate: string) => {
        e.preventDefault();
        setDragOverCell(null);
        const raw = e.dataTransfer.getData('application/json');
        if (!raw) return;
        const data = JSON.parse(raw);
        if (data.from_income_date === targetDate) return;

        // Compute balance impact from schedule data
        const fromCol = schedule?.columns?.[data.from_income_date];
        const toCol = schedule?.columns?.[targetDate];

        let itemAmount = 0;
        let itemName = `Item #${data.budget_item_id}`;
        if (fromCol) {
            const entry = fromCol.expenses.find((e: any) => e.budget_item?.id === data.budget_item_id);
            if (entry) {
                itemName = entry.budget_item?.name || itemName;
                itemAmount = entry.items.reduce((sum: number, i: any) => sum + (i.extrapolation_item?.amount ?? 0), 0);
            }
        }

        const fromTotal = fromCol ? columnTotal(fromCol) : 0;
        const toTotal = toCol ? columnTotal(toCol) : 0;
        const fromAfter = fromTotal - itemAmount;
        const toAfter = toTotal + itemAmount;

        setPendingMove({
            budget_item_id: data.budget_item_id,
            from_income_date: data.from_income_date,
            to_income_date: targetDate,
            itemName,
            itemAmount,
            fromTotal,
            toTotal,
            fromAfter,
            toAfter,
        });
    };

    const confirmMove = async () => {
        if (!pendingMove) return;
        try {
            await api.post(`/calendar/${profile?.id}/move_item`, {
                budget_item_id: pendingMove.budget_item_id,
                from_income_date: pendingMove.from_income_date,
                to_income_date: pendingMove.to_income_date,
            });
            setPendingMove(null);
            onReload();
        } catch (err) {
            alert(`Failed to move item: ${err.message}`);
            setPendingMove(null);
        }
    };

    const fmt = (n: number) => n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });

    return (
        <TableBody>
            <TableRow hover className="calendar-carry-row" style={{
                backgroundColor: monthColors[theme][12],
            }}>
                <TableCell style={{ fontWeight: 'bold' }}>Carry</TableCell>
                {(schedule?.sorted_income_dates ?? []).map((date) => (
                    <TableCell key={date + '-carry'} className="currency" style={{fontWeight: 'bold', whiteSpace: 'nowrap', minWidth: '100px'}}>
                        <CurrencyLabel amount={schedule.columns[date]?.starting_balance ?? 0} />
                    </TableCell>
                ))}
            </TableRow>
            <TableRow hover className="calendar-income-row" style={{
                backgroundColor: monthColors[theme][12],
            }}>
                <TableCell style={{ fontWeight: 'bold' }}>Income</TableCell>
                {(schedule?.sorted_income_dates ?? []).map((date) => (
                    <TableCell key={date + '-income'} className="currency" style={{
                        fontWeight: 'bold',
                        whiteSpace: 'nowrap',
                        minWidth: '100px',
                    }}>
                        <CurrencyLabel amount={schedule.columns[date].incomes[0].items[0].extrapolation_item.amount} />
                    </TableCell>
                ))}
            </TableRow>
            {schedule?.expense_budget_items.map((budgetItem) => <TableRow hover key={budgetItem.id}>
                <TableCell style={{ backgroundColor: monthColors[theme][12], fontWeight: 'bold' }}>{budgetItem.name}</TableCell>
                {schedule?.sorted_income_dates.map((date, dateIndex) => {
                    const cellKey = `${date}-${budgetItem.id}`;
                    const expense = schedule.columns[date].expenses.find((e: any) => e.budget_item.id === budgetItem.id);
                    if (expense) {
                        return (
                            <CalendarExtrapolationCell
                                key={date + '-expense'}
                                entry={expense}
                                date={date.substring(0, 7)}
                                incomeDate={date}
                                schedule={schedule}
                                setEditingCell={setEditingCell}
                                theme={theme}
                                onDrop={(e: React.DragEvent) => handleDrop(e, date)}
                                onQuickPay={handleQuickPay}
                            />
                        );
                    }
                    return (
                        <TableCell
                            key={date + '-expense'}
                            style={{
                                backgroundColor: dragOverCell === cellKey
                                    ? 'rgba(25, 118, 210, 0.15)'
                                    : monthColors[theme][getMonthByColumnIndex(dateIndex, schedule?.sorted_income_dates) + 12],
                                whiteSpace: 'nowrap',
                                minWidth: '100px',
                                outline: dragOverCell === cellKey ? '2px dashed #1976d2' : 'none',
                            }}
                            onDragOver={(e) => {
                                e.preventDefault();
                                e.dataTransfer.dropEffect = 'move';
                            }}
                            onDragEnter={(e) => {
                                e.preventDefault();
                                setDragOverCell(cellKey);
                            }}
                            onDragLeave={() => setDragOverCell(null)}
                            onDrop={(e) => handleDrop(e, date)}
                        />
                    );
                })}
            </TableRow>)}
            {miscRowCount > 0 && Array(miscRowCount).fill(0).map((_, i) => (
                <TableRow hover key={i}>
                    <TableCell
                        key={`misc-${i}`}
                        style={{
                            backgroundColor: monthColors[theme][12],
                            fontWeight: 'bold',
                        }}>
                        misc
                    </TableCell>
                    {(schedule?.sorted_income_dates ?? []).map((date, colIndex) => (
                        <TableCell
                            key={date + '-misc' + i}
                            className={`currency calendar-entry-month-${date.substring(5, 7)}`}
                            style={{
                                backgroundColor: miscEntries[date] && miscEntries[date][i] ?
                                    monthColors[theme][parseInt(date.substring(5, 7), 10) - 1] :
                                    monthColors[theme][getMonthByColumnIndex(colIndex, schedule?.sorted_income_dates) + 12],
                                fontWeight: 'bold',
                                whiteSpace: 'nowrap',
                                minWidth: '100px',
                            }}
                            onClick={() => {
                                setEditingCell(miscEntries[date] ? miscEntries[date][i] : null);
                            }}
                        >
                            {miscEntries[date] && miscEntries[date][i] ? miscEntries[date][i].amount : ''}
                        </TableCell>
                    ))}
                </TableRow>
            ))}
            <TableRow hover className="calendar-total-row" style={{
                backgroundColor: monthColors[theme][12],
                fontWeight: 'bold',
            }}>
                <TableCell style={{ fontWeight: 'bold' }}>Total</TableCell>
                {(schedule?.sorted_income_dates ?? []).map((date) => (
                    <TableCell key={date + '-total'} className="currency" style={{
                        fontWeight: 'bold',
                        whiteSpace: 'nowrap',
                        minWidth: '100px',
                    }}>
                        <CurrencyLabel amount={columnTotal(schedule.columns[date])} />
                    </TableCell>
                ))}
            </TableRow>
            <TableRow hover style={{ backgroundColor: monthColors[theme][12] }}>
                <TableCell style={{ fontWeight: 'bold' }}>Safe to Spend</TableCell>
                {(schedule?.sorted_income_dates ?? []).map((date) => {
                    const safe = columnSafeToSpend(schedule.columns[date]);
                    return (
                        <TableCell key={date + '-safe'} className="currency" style={{
                            fontWeight: 'bold',
                            whiteSpace: 'nowrap',
                            minWidth: '100px',
                            color: safe >= 0 ? '#4caf50' : '#ef5350',
                        }}>
                            <CurrencyLabel amount={safe} />
                        </TableCell>
                    );
                })}
            </TableRow>
            {/* Move confirmation dialog */}
            {pendingMove && (
                <Dialog open={!!pendingMove} onClose={() => setPendingMove(null)} maxWidth="xs" fullWidth>
                    <DialogTitle>Confirm Move</DialogTitle>
                    <DialogContent>
                        <Typography variant="body1" gutterBottom>
                            Move <strong>{pendingMove.itemName}</strong> (${fmt(Math.abs(pendingMove.itemAmount))})
                        </Typography>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                            From: {pendingMove.from_income_date} → To: {pendingMove.to_income_date}
                        </Typography>
                        <Typography variant="body2" sx={{ mt: 2 }}>
                            Source ending balance: ${fmt(pendingMove.fromTotal)} → ${fmt(pendingMove.fromAfter)}
                        </Typography>
                        <Typography variant="body2">
                            Destination ending balance: ${fmt(pendingMove.toTotal)} → ${fmt(pendingMove.toAfter)}
                        </Typography>
                        {pendingMove.toAfter < 0 && (
                            <Typography variant="body2" color="error" sx={{ mt: 1, fontWeight: 'bold' }}>
                                Warning: destination column will go negative (${fmt(pendingMove.toAfter)})
                            </Typography>
                        )}
                    </DialogContent>
                    <DialogActions>
                        <Button onClick={() => setPendingMove(null)}>Cancel</Button>
                        <Button variant="contained" onClick={confirmMove}>Move</Button>
                    </DialogActions>
                </Dialog>
            )}
        </TableBody>
    );
}
