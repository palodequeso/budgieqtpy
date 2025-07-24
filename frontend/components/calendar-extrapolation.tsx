import {
    TableBody,
    TableCell,
    TableRow
} from '@mui/material';
import * as React from 'react';
import CalendarExtrapolationCell from './calendar-extrapolation-cell';
import { monthColors } from './utils';
import CurrencyLabel from './currency-label';
import * as moment from 'moment';

export class CalendarEntry {
    public incomeDate: string;
    public budgetItem: any;
    public items: any[]; // extrapolation items, ledger entries, etc?
    public get amount(): number {
        return this.items.reduce((acc, item) => {
            return parseFloat(acc.toString()) + parseFloat(item.amount.toString());
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

export default function CalendarExtrapolation({
    // extrapolation,
    schedule,
    setEditingCell,
    theme,
    miscRowCount,
    miscEntries,
}: {
    // extrapolation: { [s: string]: CalendarIncomeColumn },
    schedule: any,
    setEditingCell: (cell: any) => void,
    theme: string,
    miscRowCount: number,
    miscEntries: any,
}) {
    const exGrid = new CalendarExtrapolationGrid(schedule.sorted_income_dates, schedule);

    return (
        <TableBody>
            <TableRow hover className="calendar-carry-row" style={{
                backgroundColor: monthColors[theme][12],
            }}>
                <TableCell style={{ fontWeight: 'bold' }}>Carry</TableCell>
                {(schedule?.sorted_income_dates ?? []).map((date) => (
                    <TableCell key={date + '-carry'} className="currency" style={{fontWeight: 'bold'}}>
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
                    }}>
                        <CurrencyLabel amount={schedule.columns[date].incomes[0].items[0].extrapolation_item.amount} />
                    </TableCell>
                ))}
                    {/* }}
                    {(schedule?.schedule.income_budget_items ?? []).map((date) => (
                        <TableCell key={date + '-income'} className="currency" style={{
                            fontWeight: 'bold',
                        }}>
                            <CurrencyLabel amount={schedule.columns[date].incomes[0].items[0].extrapolation_item.amount} />
                        </TableCell>
                    ))} */}
            </TableRow>
            {schedule?.expense_budget_items.map((budgetItem, rowIndex) => <TableRow hover key={budgetItem.id}>
                <TableCell style={{ backgroundColor: monthColors[theme][12], fontWeight: 'bold' }}>{budgetItem.name}</TableCell>
                {/*<CalendarExtrapolationCell */}
                {schedule?.sorted_income_dates.map((date) => (
                    <TableCell key={date + '-expense'} className="currency" style={{
                        fontWeight: 'bold',
                    }}>
                        <CurrencyLabel amount={schedule.columns[date].expenses.find((e: any) => e.budget_item.id === budgetItem.id)?.items.reduce((acc: any, item: any) => acc + item.extrapolation_item.amount, 0) ?? 0} />
                    </TableCell>
                ))}
                {/* {exGrid.grid[rowIndex].map((entry: CalendarEntry | null, colIndex) => entry ? <CalendarExtrapolationCell
                    key={`empty-${rowIndex}-${colIndex}`}
                    entry={entry}
                    date={entry.incomeDate}
                    schedule={schedule}
                    setEditingCell={setEditingCell}
                    theme={theme}
                /> :
                    <TableCell key={`empty-${rowIndex}-${colIndex}`} style={{ backgroundColor: monthColors[theme][getMonthByColumnIndex(colIndex, exGrid.sortedIncomeDates) + 12] }}></TableCell>)} */}
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
                                    monthColors[theme][getMonthByColumnIndex(colIndex, exGrid.sortedIncomeDates) + 12],
                                fontWeight: 'bold',
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
                    }}>
                        {/* <CurrencyLabel amount={extrapolation[date].total} /> */}
                    </TableCell>
                ))}
            </TableRow>
        </TableBody>
    );
}
