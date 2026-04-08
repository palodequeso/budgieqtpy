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

export default function Calendar() {
    const [schedule, setSchedule] = React.useState<any>(null);
    const [extrapolation, setExtrapolation] = React.useState<{ [s: string]: CalendarIncomeColumn }>({});
    const [unscheduledItems, setUnscheduledItems] = React.useState([]);
    const [miscEntries, setMiscEntries] = React.useState({});
    const [miscRowCount, setMiscRowCount] = React.useState(0);
    const [editingCell, setEditingCell] = React.useState<CalendarEntry | null>(null);
    const [isLoading, setIsLoading] = React.useState(true);
    const [fetchError, setFetchError] = React.useState(null);
    const [theme, setTheme] = React.useState(localStorage.getItem('budgie:theme') || 'dark');
    const [showAllColumns, setShowAllColumns] = React.useState(false);
    const profile = useStore((state) => (state as any).profile);
    const todayHeaderRef = React.useRef<HTMLTableCellElement | null>(null);

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

            setSchedule(json);

            // Extract unscheduled items from schedule response.
            // Map raw extrapolation items to the shape the unscheduled dialog expects:
            //   { id, budgetItem: { name }, date, amount, incomeDate }
            const budgetItemMap: Record<number, any> = {};
            for (const bi of (json.budget_item_list || [])) {
                budgetItemMap[bi.id] = bi;
            }
            const unscheduled = (json.extrapolation_items || [])
                .filter((item: any) => !item.income_date)
                .map((item: any) => ({
                    id: item.id,
                    budgetItem: budgetItemMap[item.budget_item_id] || { name: 'Unknown' },
                    date: item.due_date,
                    amount: item.amount,
                    incomeDate: null,
                }));
            setUnscheduledItems(unscheduled);

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

    // Filter visible income dates based on profile.hidden_through
    const getVisibleIncomeDates = () => {
        if (!schedule?.sorted_income_dates) return [];
        
        // If showing all columns or no hidden_through, show all dates
        if (showAllColumns || !profile?.hidden_through) {
            return schedule.sorted_income_dates;
        }
        
        // Filter out dates <= hidden_through
        const hiddenDate = new Date(profile.hidden_through);
        return schedule.sorted_income_dates.filter(dateStr => {
            const date = new Date(dateStr);
            return date > hiddenDate;
        });
    };

    const visibleIncomeDates = getVisibleIncomeDates();

    // Determine the "today" column (last income_date <= today)
    const today = new Date().toISOString().slice(0, 10);
    const todayColumnDate = React.useMemo(() => {
        let result: string | null = null;
        for (const d of visibleIncomeDates) {
            if (d <= today) {
                result = d;
            } else {
                break;
            }
        }
        return result;
    }, [visibleIncomeDates, today]);

    // Auto-scroll to the current period header after loading
    React.useEffect(() => {
        if (!isLoading && todayHeaderRef.current) {
            todayHeaderRef.current.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
        }
    }, [isLoading, todayColumnDate]);

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
                        schedule={schedule}
                        showAllColumns={showAllColumns}
                        setShowAllColumns={setShowAllColumns}
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
                                                {visibleIncomeDates.map((date) => {
                                                        const isTodayCol = date === todayColumnDate;
                                                        return (
                                                            <TableCell
                                                                ref={isTodayCol ? todayHeaderRef : undefined}
                                                                style={{
                                                                    fontSize: '11px',
                                                                    fontWeight: isTodayCol ? 'bold' : undefined,
                                                                    borderLeft: isTodayCol ? '3px solid #1976d2' : undefined,
                                                                    backgroundColor: isTodayCol ? (theme === 'dark' ? '#1a3a5c' : '#bbdefb') : undefined,
                                                                }}
                                                                key={date}
                                                            >
                                                                {isTodayCol && <span style={{ color: '#1976d2', marginRight: 4 }}>&#9658;</span>}
                                                                {<DateLabel date={date} />}
                                                            </TableCell>
                                                        );
                                                    })}
                                            </TableRow>
                                        </TableHead>
                                        {schedule ? (
                                            <CalendarExtrapolation
                                                schedule={{...schedule, sorted_income_dates: visibleIncomeDates}}
                                                setEditingCell={setEditingCell}
                                                theme={theme}
                                                miscEntries={miscEntries}
                                                miscRowCount={miscRowCount}
                                                onReload={load}
                                            />
                                        ) : (
                                            <TableBody></TableBody>
                                        )}
                                        <TableBody></TableBody>
                                    </Table>
                                </ScrollContainer>
                            </TableContainer>
                        )}
                        {/* <CalendarSummary
                            sortedIncomeDates={schedule?.sorted_income_dates ?? []}
                            profile={profile}
                        /> */}
                        {fetchError && (
                            <div style={{ color: 'red', padding: '16px', textAlign: 'center' }}>
                                {fetchError}
                            </div>
                        )}
                    </div>
                </div>
            )}
            {profile && (
                <div style={{ padding: '16px', textAlign: 'center' }}>
                    <a 
                        href={`/api/calendar/${profile.id}/downloadspreadsheet`}
                        style={{ 
                            color: '#1976d2', 
                            textDecoration: 'none',
                            fontSize: '14px',
                            fontWeight: '500'
                        }}
                    >
                        📥 Download Schedule Spreadsheet
                    </a>
                </div>
            )}
        </Paper>
    );
}
