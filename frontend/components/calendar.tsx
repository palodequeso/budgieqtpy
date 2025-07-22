// import SnackbarUnstyled from '@mui/base/SnackbarUnstyled';
import { CircularProgress } from '@mui/material';
import Paper from '@mui/material/Paper';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import * as React from 'react';
import CalendarControls from './calendar-controls';
import CalendarExtrapolation from './calendar-extrapolation';
import { CalendarIncomeColumn, CalendarEntry } from './calendar-extrapolation';
import CalendarSummary from './calendar-summary';
import DateLabel from './date-label';
import NoData from './nodata';
import { api } from './renderUtils';
import ScrollContainer from 'react-indiana-drag-scroll';
import { useStore } from '../store';

function sortableDate(dateStr) {
    const date = dateStr ? new Date(dateStr) : new Date();
    return date.toISOString().substring(0, 10);
}

function formatExtrapolationData(data: any, startingBalance: number): any {
    const out: { [s: string]: CalendarIncomeColumn } = {};
    const unscheduled: any[] = [];

    for (const extrapolationItem of data.extrapolation) {
        if (!extrapolationItem.incomeDate) {
            unscheduled.push(extrapolationItem);
            continue;
        }

        const date = sortableDate(extrapolationItem.incomeDate);
        if (!out[date]) {
            out[date] = new CalendarIncomeColumn(extrapolationItem.incomeDate);
        }

        const previousEntry = out[date].entries.find(e => e.budgetItem.id === extrapolationItem.budgetItem.id);
        if (previousEntry) {
            previousEntry.items.push(extrapolationItem);
        } else {
            const entry: CalendarEntry = new CalendarEntry();
            entry.items = [extrapolationItem];
            entry.budgetItem = { ...extrapolationItem.budgetItem };
            entry.incomeDate = extrapolationItem.incomeDate;
            out[date].entries.push(entry);
        }
    }

    for (const oneOff of data.oneOffExtrapolationItems) {
        const date = sortableDate(oneOff.incomeDate);
        if (!out[date]) {
            out[date] = new CalendarIncomeColumn(oneOff.incomeDate);
        }
        const calendarEntry = new CalendarEntry();
        calendarEntry.items = [oneOff];
        calendarEntry.budgetItem = null;
        calendarEntry.incomeDate = oneOff.incomeDate;
        out[date].entries.push(calendarEntry);
    }

    // for (const ledgerEntry of data.ledgerEntries) {
    //     const incomeDate = sortableDate(ledgerEntry.incomeDate);
    //     console.log('ledger entry', ledgerEntry, incomeDate);
    // }

    const sortedDates = Object.keys(out).sort();

    // for (const miscLedgerEntry of data.miscLedgerEntries) {
    //     const incomeDate = sortableDate(miscLedgerEntry.incomeDate);
    //     console.log('misc ledger entry', miscLedgerEntry, incomeDate);
    // }

    // for (const item of data.ledgerEntries) {
    //     const incomeDate = sortableDate(item.incomeDate);
    //     if (out[incomeDate]) {
    //         // out[incomeDate].entries.push({
    //         //     id: `ledger-${item.id}`,
    //         //     amount: item.amount,
    //         //     budgetItem: item.budgetItem,
    //         //     date: item.date,
    //         //     incomeDate: item.incomeDate,
    //         //     ledgerEntry: item,
    //         // });
    //         // out[incomeDate].subTotal += parseFloat(item.amount);
    //     }
    // }

    // for (const miscLedgerEntry of data.miscLedgerEntries) {
    //     const ledgerDate = sortableDate(miscLedgerEntry.date);
    //     let previousIncomeDate = '';
    //     for (const incomeDate of sortedDates) {
    //         if (incomeDate < ledgerDate) {
    //             previousIncomeDate = incomeDate;
    //         }
    //     }
    //     if (previousIncomeDate) {
    //         // out[previousIncomeDate].entries.push({
    //         //     id: `ledger-${miscLedgerEntry.id}`,
    //         //     amount: miscLedgerEntry.amount,
    //         //     budgetItem: { id: null, name: miscLedgerEntry.name },
    //         //     date: miscLedgerEntry.date,
    //         //     incomeDate: previousIncomeDate,
    //         //     ledgerEntry: miscLedgerEntry,
    //         // });
    //         // out[previousIncomeDate].subTotal += parseFloat(
    //         //     miscLedgerEntry.amount,
    //         // );
    //     }
    // }

    let previousDate: null | string = null;
    let sortedOut: { [s: string]: CalendarIncomeColumn } = {};
    sortedDates.forEach((date) => {
        if (previousDate && out[previousDate]) {
            out[date].carry = out[previousDate].total;
        } else {
            out[date].carry = startingBalance;
        }

        const incomeIndex = out[date].entries.findIndex(
            (entry) => entry.budgetItem.type === 'income',
        );
        if (incomeIndex !== -1) {
            previousDate = date;
        }
        out[date].income = null;
        if (incomeIndex > -1) {
            out[date].income = out[date].entries[incomeIndex];
            out[date].entries.splice(incomeIndex, 1);
            sortedOut[date] = out[date];
        } else {
            // HAX!! TODO
            delete out[date];
        }
    });

    return {
        sorted: sortedOut,
        unscheduled,
    };
}

export default function Calendar() {
    const [extrapolation, setExtrapolation] = React.useState<{ [s: string]: CalendarIncomeColumn }>({});
    const [unscheduledItems, setUnscheduledItems] = React.useState([]);
    const [miscEntries, setMiscEntries] = React.useState({});
    const [miscRowCount, setMiscRowCount] = React.useState(0);
    const [editingCell, setEditingCell] = React.useState<CalendarEntry | null>(null);
    const [isLoading, setIsLoading] = React.useState(true);
    const [fetchError, setFetchError] = React.useState(null);
    const theme = localStorage.getItem('budgie:theme') || 'light';
    const profile = useStore((state) => (state as any).profile);

    const extrapolate = async () => {
        if (!profile) {
            return;
        }
        try {
            setIsLoading(true);
            await api.post(`/extrapolate/${profile.id}`, {
                profileID: profile.id,
            });
            await load();
        } catch (e) {
            setFetchError(e.message);
        }
    };

    const load = async () => {
        if (!profile) {
            return;
        }

        setIsLoading(true);

        try {
            const json = await api.get(`/schedule/${profile.id}`);
            const startingBalance = profile.accounts.reduce((carry, account) => {
                return parseFloat(carry) + parseFloat(account.balance);
            }, 0);
            const { sorted, unscheduled } = formatExtrapolationData(json, startingBalance);
            setExtrapolation(sorted);
            setUnscheduledItems(unscheduled);

            const miscEntries = {};
            let maxRows = 0;
            for (const date of Object.keys(sorted)) {
                for (const entry of sorted[date].entries) {
                    if (!entry.budgetItem || entry.budgetItem.id === null) {
                        if (!miscEntries[date]) {
                            miscEntries[date] = [];
                        }
                        miscEntries[date].push(entry);
                        if (miscEntries[date].length > maxRows) {
                            maxRows = miscEntries[date].length;
                        }
                    }
                }
            }
            setMiscRowCount(maxRows);
            setMiscEntries(miscEntries);

            const elements: HTMLDivElement[] = [];
            let maxHeight = 0;
            document.querySelectorAll('.calendar-column').forEach((el) => {
                elements.push(el as HTMLDivElement);
                maxHeight = Math.max(maxHeight, el.clientHeight);
            });
            elements.forEach((el) => {
                (el as HTMLDivElement).style.height = `${maxHeight}px`;
                (el as HTMLDivElement).style.width = '200px';
            });
            setIsLoading(false);
        } catch (e) {
            console.error('behold, a fetch error', e);
            setFetchError(e.message);
        }
    };

    React.useEffect(() => {
        load();
    }, [profile]);

    return (
        <Paper className="section" id="calendar" elevation={2}>
            {profile && profile?.budget?.length === 0 ? (
                <NoData />
            ) : (
                <div>
                    <CalendarControls
                        unscheduledItems={unscheduledItems}
                        extrapolate={extrapolate}
                        extrapolation={extrapolation}
                        editingCell={editingCell}
                        setEditingCell={setEditingCell}
                        load={load}
                    />
                    <div>
                        {isLoading ? (
                            <CircularProgress />
                        ) : (
                            <TableContainer
                                id="calendar-table-container"
                                component={Paper}
                            >
                                <ScrollContainer vertical={true} horizontal={true} hideScrollbars={false}>
                                    <Table stickyHeader size="small">
                                        <TableHead>
                                            <TableRow hover>
                                                <TableCell></TableCell>
                                                {extrapolation
                                                    ? Object.keys(
                                                        extrapolation,
                                                    ).map((date) => {
                                                        return (
                                                            <TableCell
                                                                style={{
                                                                    fontSize:
                                                                        '11px',
                                                                }}
                                                                key={date}
                                                            >
                                                                {<DateLabel date={date} />}
                                                            </TableCell>
                                                        );
                                                    })
                                                    : null}
                                            </TableRow>
                                        </TableHead>
                                        {extrapolation ? (
                                            <CalendarExtrapolation
                                                extrapolation={extrapolation}
                                                setEditingCell={setEditingCell}
                                                theme={theme}
                                                miscEntries={miscEntries}
                                                miscRowCount={miscRowCount}
                                            />
                                        ) : (
                                            <TableBody></TableBody>
                                        )}
                                        <TableBody></TableBody>
                                    </Table>
                                </ScrollContainer>
                            </TableContainer>
                        )}
                        <CalendarSummary
                            sortedIncomeDates={Object.keys(extrapolation).sort()}
                            profile={profile}
                        />
                        {/* <SnackbarUnstyled */}
                        <div
                            // open={fetchError !== null}
                            // autoHideDuration={5000}
                            // onClose={() => setFetchError(null)}
                        >
                            {fetchError}
                        {/* </SnackbarUnstyled> */}
                        </div>
                    </div>
                </div>
            )}
            {/* <a href={`/api/calendar/${profile.id}/downloadspreadsheet`}>Download</a> */}
            <div>Ledger Recent</div>
            <div>Upcoming Entries</div>
        </Paper>
    );
}
