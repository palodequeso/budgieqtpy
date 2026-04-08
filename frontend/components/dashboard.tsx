import * as React from 'react';
import {
    Alert,
    Box,
    Button,
    CircularProgress,
    FormControl,
    InputLabel,
    MenuItem,
    Paper,
    Select,
    Snackbar,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    TextField,
    Typography,
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { api } from './renderUtils';
import { useStore } from '../store';
import CurrencyLabel from './currency-label';

interface DashboardItem {
    id: number;
    name: string;
    type: string;
    amount: number;
    due_date: string;
    income_date: string | null;
    budget_item_id: number | null;
    is_paid: boolean;
    category: string | null;
}

interface DashboardColumn {
    income_date: string;
    income: number;
    expenses: number;
    paid_expenses: number;
    starting_balance: number;
    safe_to_spend: number;
    ending_balance: number;
}

interface DashboardData {
    upcoming: DashboardItem[];
    overdue: DashboardItem[];
    current_column: DashboardColumn | null;
    columns: DashboardColumn[];
    total_unpaid: number;
    total_paid: number;
    account_count: number;
    budget_item_count: number;
}

export default function Dashboard() {
    const theme = useTheme();
    const profile = useStore((state) => (state as any).profile);
    const accounts = useStore((state) => (state as any).accounts);

    const [data, setData] = React.useState<DashboardData | null>(null);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState<string | null>(null);

    // Quick add expense state
    const [expenseName, setExpenseName] = React.useState('');
    const [expenseAmount, setExpenseAmount] = React.useState('');
    const [expenseAccountId, setExpenseAccountId] = React.useState<number | ''>('');
    const [successMsg, setSuccessMsg] = React.useState<string | null>(null);

    // Mark paid account selections (keyed by item id)
    const [payAccountSelections, setPayAccountSelections] = React.useState<Record<number, number>>({});

    const isDark = theme.palette.mode === 'dark';
    const headerBg = isDark ? '#263238' : '#e0e0e0';
    const contentBg = isDark ? '#37474f' : '#f5f5f5';

    const fetchDashboard = React.useCallback(async () => {
        if (!profile) return;
        try {
            setLoading(true);
            setError(null);
            const result = await api.get(`/dashboard/${profile.id}`);
            setData(result as DashboardData);
        } catch (e: any) {
            setError(e.message || 'Failed to load dashboard');
        } finally {
            setLoading(false);
        }
    }, [profile?.id]);

    React.useEffect(() => {
        fetchDashboard();
    }, [fetchDashboard]);

    const handleMarkPaid = async (item: DashboardItem) => {
        const accountId = payAccountSelections[item.id];
        if (!accountId) return;
        try {
            await api.post(`/budget/markpaid/${profile.id}`, {
                extrapolationItemId: item.id,
                accountId,
            });
            await fetchDashboard();
        } catch (e: any) {
            setError(e.message || 'Failed to mark paid');
        }
    };

    const handleQuickAdd = async () => {
        if (!expenseName || !expenseAmount || !data?.current_column) return;
        try {
            await api.post(`/calendar/${profile.id}/oneoff`, {
                name: expenseName,
                amount: parseFloat(expenseAmount),
                type: 'expense',
                incomeDate: data.current_column.income_date,
                addingOneOffExpensePaid: true,
                account: expenseAccountId || undefined,
            });
            setExpenseName('');
            setExpenseAmount('');
            setExpenseAccountId('');
            setSuccessMsg('Expense added successfully');
            await fetchDashboard();
        } catch (e: any) {
            setError(e.message || 'Failed to add expense');
        }
    };

    const daysUntil = (dateStr: string) => {
        const due = new Date(dateStr + 'T00:00:00');
        const now = new Date();
        now.setHours(0, 0, 0, 0);
        return Math.ceil((due.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
    };

    const formatDate = (dateStr: string) => {
        const d = new Date(dateStr + 'T00:00:00');
        return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
    };

    const today = new Date().toLocaleDateString(undefined, {
        weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
    });

    const renderAccountSelect = (itemId: number, size: 'small' | 'medium' = 'small') => (
        <FormControl size={size} sx={{ minWidth: 120 }}>
            <InputLabel>Account</InputLabel>
            <Select
                value={payAccountSelections[itemId] || ''}
                label="Account"
                onChange={(e) => setPayAccountSelections(prev => ({
                    ...prev,
                    [itemId]: e.target.value as number,
                }))}
            >
                {(accounts || []).map((acc: any) => (
                    <MenuItem key={acc.id} value={acc.id}>{acc.name}</MenuItem>
                ))}
            </Select>
        </FormControl>
    );

    if (loading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 300 }}>
                <CircularProgress />
            </Box>
        );
    }

    if (error && !data) {
        return (
            <Box sx={{ p: 3 }}>
                <Alert severity="error">{error}</Alert>
            </Box>
        );
    }

    const currentCol = data?.current_column;
    const safeToSpend = currentCol?.safe_to_spend ?? 0;
    const isPositive = safeToSpend >= 0;

    return (
        <Box sx={{ p: 3, maxWidth: 1200, margin: '0 auto' }}>
            {/* Error snackbar */}
            {error && (
                <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
                    {error}
                </Alert>
            )}

            {/* Success snackbar */}
            <Snackbar
                open={!!successMsg}
                autoHideDuration={3000}
                onClose={() => setSuccessMsg(null)}
                anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
            >
                <Alert severity="success" onClose={() => setSuccessMsg(null)}>
                    {successMsg}
                </Alert>
            </Snackbar>

            {/* Header */}
            <Paper elevation={2} sx={{ p: 0, mb: 3 }}>
                <Box sx={{
                    backgroundColor: headerBg,
                    borderRadius: '8px 8px 0 0',
                    padding: '15px 20px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                }}>
                    <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                        Dashboard
                    </Typography>
                    <Typography variant="body1" sx={{ opacity: 0.8 }}>
                        {today}
                    </Typography>
                </Box>

                {/* Safe to Spend Hero */}
                {currentCol && (
                    <Box sx={{
                        p: 3,
                        backgroundColor: contentBg,
                        borderLeft: `6px solid ${isPositive ? '#4caf50' : '#f44336'}`,
                        borderRadius: '0 0 8px 8px',
                    }}>
                        <Typography variant="subtitle2" sx={{ opacity: 0.7, mb: 0.5 }}>
                            Safe to Spend — Pay Period {formatDate(currentCol.income_date)}
                        </Typography>
                        <Typography
                            variant="h3"
                            sx={{
                                fontWeight: 'bold',
                                color: isPositive ? '#4caf50' : '#f44336',
                                mb: 1,
                            }}
                        >
                            <CurrencyLabel amount={safeToSpend} />
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 4 }}>
                            <Box>
                                <Typography variant="caption" sx={{ opacity: 0.6 }}>Starting Balance</Typography>
                                <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
                                    <CurrencyLabel amount={currentCol.starting_balance} />
                                </Typography>
                            </Box>
                            <Box>
                                <Typography variant="caption" sx={{ opacity: 0.6 }}>Income</Typography>
                                <Typography variant="body1" sx={{ fontWeight: 'bold', color: '#4caf50' }}>
                                    <CurrencyLabel amount={currentCol.income} />
                                </Typography>
                            </Box>
                            <Box>
                                <Typography variant="caption" sx={{ opacity: 0.6 }}>Expenses</Typography>
                                <Typography variant="body1" sx={{ fontWeight: 'bold', color: '#f44336' }}>
                                    <CurrencyLabel amount={currentCol.expenses} />
                                </Typography>
                            </Box>
                            <Box>
                                <Typography variant="caption" sx={{ opacity: 0.6 }}>Ending Balance</Typography>
                                <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
                                    <CurrencyLabel amount={currentCol.ending_balance} />
                                </Typography>
                            </Box>
                        </Box>
                    </Box>
                )}

                {!currentCol && (
                    <Box sx={{ p: 3, backgroundColor: contentBg, borderRadius: '0 0 8px 8px' }}>
                        <Typography variant="body1" sx={{ opacity: 0.6 }}>
                            No pay period data available. Run an extrapolation from the Calendar to populate your dashboard.
                        </Typography>
                    </Box>
                )}
            </Paper>

            {/* Overdue Items */}
            {data && data.overdue.length > 0 && (
                <Paper elevation={2} sx={{ mb: 3, overflow: 'hidden' }}>
                    <Box sx={{
                        backgroundColor: isDark ? '#4a1c1c' : '#ffebee',
                        padding: '12px 20px',
                        borderRadius: '8px 8px 0 0',
                    }}>
                        <Typography variant="h6" sx={{ fontWeight: 'bold', color: '#f44336' }}>
                            Overdue Items ({data.overdue.length})
                        </Typography>
                    </Box>
                    <Box sx={{ backgroundColor: contentBg, p: 2 }}>
                        {data.overdue.map((item) => (
                            <Box key={item.id} sx={{
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'space-between',
                                p: 1.5,
                                mb: 1,
                                borderRadius: 1,
                                backgroundColor: isDark ? '#3e2723' : '#fff3e0',
                                '&:last-child': { mb: 0 },
                            }}>
                                <Box>
                                    <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
                                        {item.name}
                                    </Typography>
                                    <Typography variant="body2" sx={{ opacity: 0.7 }}>
                                        Due: {formatDate(item.due_date)}
                                    </Typography>
                                </Box>
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                                    <Typography variant="body1" sx={{ fontWeight: 'bold', color: '#f44336' }}>
                                        <CurrencyLabel amount={item.amount} />
                                    </Typography>
                                    {renderAccountSelect(item.id)}
                                    <Button
                                        variant="contained"
                                        color="error"
                                        size="small"
                                        disabled={!payAccountSelections[item.id]}
                                        onClick={() => handleMarkPaid(item)}
                                    >
                                        Mark Paid
                                    </Button>
                                </Box>
                            </Box>
                        ))}
                    </Box>
                </Paper>
            )}

            {/* Upcoming Items */}
            {data && data.upcoming.length > 0 && (
                <Paper elevation={2} sx={{ mb: 3, overflow: 'hidden' }}>
                    <Box sx={{
                        backgroundColor: headerBg,
                        padding: '12px 20px',
                        borderRadius: '8px 8px 0 0',
                    }}>
                        <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                            Upcoming (Next 7 Days)
                        </Typography>
                    </Box>
                    <Box sx={{ backgroundColor: contentBg, p: 2 }}>
                        {data.upcoming.map((item) => {
                            const days = daysUntil(item.due_date);
                            return (
                                <Box key={item.id} sx={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'space-between',
                                    p: 1.5,
                                    mb: 1,
                                    borderRadius: 1,
                                    backgroundColor: isDark ? '#2e3b42' : '#ffffff',
                                    '&:last-child': { mb: 0 },
                                }}>
                                    <Box>
                                        <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
                                            {item.name}
                                        </Typography>
                                        <Typography variant="body2" sx={{ opacity: 0.7 }}>
                                            {formatDate(item.due_date)} — {days === 0 ? 'Today' : days === 1 ? 'Tomorrow' : `${days} days`}
                                        </Typography>
                                    </Box>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                                        <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
                                            <CurrencyLabel amount={item.amount} />
                                        </Typography>
                                        {renderAccountSelect(item.id)}
                                        <Button
                                            variant="contained"
                                            color="primary"
                                            size="small"
                                            disabled={!payAccountSelections[item.id]}
                                            onClick={() => handleMarkPaid(item)}
                                        >
                                            Mark Paid
                                        </Button>
                                    </Box>
                                </Box>
                            );
                        })}
                    </Box>
                </Paper>
            )}

            {/* Quick Add Expense */}
            <Paper elevation={2} sx={{ mb: 3, overflow: 'hidden' }}>
                <Box sx={{
                    backgroundColor: headerBg,
                    padding: '12px 20px',
                    borderRadius: '8px 8px 0 0',
                }}>
                    <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                        Quick Add Expense
                    </Typography>
                </Box>
                <Box sx={{
                    backgroundColor: contentBg,
                    p: 2,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 2,
                    flexWrap: 'wrap',
                }}>
                    <TextField
                        label="Name"
                        size="small"
                        value={expenseName}
                        onChange={(e) => setExpenseName(e.target.value)}
                        sx={{ minWidth: 160 }}
                    />
                    <TextField
                        label="Amount"
                        size="small"
                        type="number"
                        value={expenseAmount}
                        onChange={(e) => setExpenseAmount(e.target.value)}
                        sx={{ minWidth: 120 }}
                    />
                    <FormControl size="small" sx={{ minWidth: 140 }}>
                        <InputLabel>Account</InputLabel>
                        <Select
                            value={expenseAccountId}
                            label="Account"
                            onChange={(e) => setExpenseAccountId(e.target.value as number)}
                        >
                            {(accounts || []).map((acc: any) => (
                                <MenuItem key={acc.id} value={acc.id}>{acc.name}</MenuItem>
                            ))}
                        </Select>
                    </FormControl>
                    <Button
                        variant="contained"
                        color="primary"
                        disabled={!expenseName || !expenseAmount || !data?.current_column}
                        onClick={handleQuickAdd}
                    >
                        Add Expense
                    </Button>
                </Box>
            </Paper>

            {/* Pay Period Overview */}
            {data && data.columns.length > 0 && (
                <Paper elevation={2} sx={{ mb: 3, overflow: 'hidden' }}>
                    <Box sx={{
                        backgroundColor: headerBg,
                        padding: '12px 20px',
                        borderRadius: '8px 8px 0 0',
                    }}>
                        <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                            Pay Period Overview
                        </Typography>
                    </Box>
                    <TableContainer sx={{ backgroundColor: contentBg }}>
                        <Table size="small">
                            <TableHead>
                                <TableRow>
                                    <TableCell sx={{ fontWeight: 'bold' }}>Pay Date</TableCell>
                                    <TableCell align="right" sx={{ fontWeight: 'bold' }}>Income</TableCell>
                                    <TableCell align="right" sx={{ fontWeight: 'bold' }}>Expenses</TableCell>
                                    <TableCell align="right" sx={{ fontWeight: 'bold' }}>Safe to Spend</TableCell>
                                    <TableCell align="right" sx={{ fontWeight: 'bold' }}>Ending Balance</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {data.columns.map((col) => {
                                    const isCurrent = currentCol && col.income_date === currentCol.income_date;
                                    const colPositive = col.safe_to_spend >= 0;
                                    return (
                                        <TableRow
                                            key={col.income_date}
                                            sx={{
                                                backgroundColor: isCurrent
                                                    ? (isDark ? '#1b3a4b' : '#e3f2fd')
                                                    : 'inherit',
                                            }}
                                        >
                                            <TableCell>
                                                {formatDate(col.income_date)}
                                                {isCurrent && (
                                                    <Typography
                                                        component="span"
                                                        variant="caption"
                                                        sx={{ ml: 1, opacity: 0.7 }}
                                                    >
                                                        (current)
                                                    </Typography>
                                                )}
                                            </TableCell>
                                            <TableCell align="right" sx={{ color: '#4caf50' }}>
                                                <CurrencyLabel amount={col.income} />
                                            </TableCell>
                                            <TableCell align="right" sx={{ color: '#f44336' }}>
                                                <CurrencyLabel amount={col.expenses} />
                                            </TableCell>
                                            <TableCell
                                                align="right"
                                                sx={{
                                                    fontWeight: 'bold',
                                                    color: colPositive ? '#4caf50' : '#f44336',
                                                }}
                                            >
                                                <CurrencyLabel amount={col.safe_to_spend} />
                                            </TableCell>
                                            <TableCell align="right">
                                                <CurrencyLabel amount={col.ending_balance} />
                                            </TableCell>
                                        </TableRow>
                                    );
                                })}
                            </TableBody>
                        </Table>
                    </TableContainer>
                </Paper>
            )}
        </Box>
    );
}
