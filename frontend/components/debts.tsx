import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import {
    Alert, Box, Button, Dialog, DialogActions, DialogContent, DialogContentText,
    DialogTitle, Grid, IconButton, MenuItem, Paper, Select, Table, TableBody, TableCell, TableContainer,
    TableHead, TableRow, TextField, Typography
} from '@mui/material';
import * as React from 'react';
import { useTheme } from '@mui/material/styles';
import { api } from './renderUtils';
import HelpIcon from './help-icon';
import { fetchProfile, useStore } from '../store';

interface Debt {
    id: number;
    name: string;
    total_amount: number;
    remaining_amount: number;
    min_payment: number;
    interest_rate: number;
    profile_id: number;
    created_at: string;
}

interface DebtPaymentEntry {
    debt_id: number;
    debt_name: string;
    amount: number;
    income_date: string;
}

const emptyForm = {
    name: '',
    total_amount: 0,
    remaining_amount: 0,
    min_payment: 0,
    interest_rate: 0,
};

export default function Debts() {
    const theme = useTheme();
    const profile = useStore((state) => (state as any).profile);

    const [debts, setDebts] = React.useState<Debt[]>([]);
    const [error, setError] = React.useState<string | null>(null);
    const [showForm, setShowForm] = React.useState(false);
    const [editingDebtId, setEditingDebtId] = React.useState<number | null>(null);
    const [form, setForm] = React.useState({ ...emptyForm });

    // Delete confirmation
    const [deleteDialogOpen, setDeleteDialogOpen] = React.useState(false);
    const [debtToDelete, setDebtToDelete] = React.useState<Debt | null>(null);

    // Compute payments
    const [savingsMargin, setSavingsMargin] = React.useState<number>(0);
    const [computedPayments, setComputedPayments] = React.useState<DebtPaymentEntry[] | null>(null);
    const [computeError, setComputeError] = React.useState<string | null>(null);
    const [saveSuccess, setSaveSuccess] = React.useState<string | null>(null);
    // Available income dates from the last computation (for the add-row dropdown)
    const [availableIncomeDates, setAvailableIncomeDates] = React.useState<string[]>([]);

    const fetchDebts = async () => {
        try {
            const res = await api.get(`/debts/${profile.id}`);
            setDebts(res as Debt[]);
        } catch (err) {
            setError(err.message);
        }
    };

    React.useEffect(() => {
        if (profile?.id) {
            fetchDebts();
        }
    }, [profile?.id]);

    const resetForm = () => {
        setForm({ ...emptyForm });
        setEditingDebtId(null);
        setShowForm(false);
    };

    const [success, setSuccess] = React.useState<string | null>(null);

    const handleSubmit = async () => {
        try {
            if (editingDebtId) {
                await api.put(`/debts/${profile.id}/${editingDebtId}`, form);
                setSuccess(`Debt '${form.name}' updated successfully!`);
            } else {
                await api.post(`/debts/${profile.id}`, form);
                setSuccess(`Debt '${form.name}' created successfully!`);
            }
            setTimeout(() => setSuccess(null), 3000);
            resetForm();
            fetchDebts();
        } catch (err) {
            setError(err.message);
        }
    };

    const startEdit = (debt: Debt) => {
        setForm({
            name: debt.name,
            total_amount: debt.total_amount,
            remaining_amount: debt.remaining_amount,
            min_payment: debt.min_payment,
            interest_rate: debt.interest_rate,
        });
        setEditingDebtId(debt.id);
        setShowForm(true);
    };

    const confirmDelete = (debt: Debt) => {
        setDebtToDelete(debt);
        setDeleteDialogOpen(true);
    };

    const handleDelete = async () => {
        if (!debtToDelete) return;
        try {
            const name = debtToDelete.name;
            await api.delete(`/debts/${profile.id}/${debtToDelete.id}`);
            setDeleteDialogOpen(false);
            setDebtToDelete(null);
            setSuccess(`Debt '${name}' deleted.`);
            setTimeout(() => setSuccess(null), 3000);
            fetchDebts();
        } catch (err) {
            setError(err.message);
        }
    };

    const computePayments = async () => {
        try {
            setComputeError(null);
            setSaveSuccess(null);
            const res = await api.post(`/debts/${profile.id}/compute`, {
                savings_margin: savingsMargin,
            });
            const payments = (res as any).payments || [];
            setComputedPayments(payments);
            // Collect unique income dates for the add-row dropdown
            const dates = [...new Set(payments.map((p: DebtPaymentEntry) => p.income_date))] as string[];
            dates.sort();
            setAvailableIncomeDates(dates);
        } catch (err) {
            setComputeError(err.message);
        }
    };

    const savePayments = async () => {
        if (!computedPayments) return;
        try {
            const res = await api.post(`/debts/${profile.id}/save_payments`, {
                payments: computedPayments,
            });
            setSaveSuccess(`Saved ${(res as any).count} payment(s) successfully.`);
            setComputedPayments(null);
            // Refresh profile so calendar picks up new extrapolation items
            fetchProfile(profile.id.toString());
        } catch (err) {
            setComputeError(err.message);
        }
    };

    // --- Payment editing helpers ---
    const updatePaymentAmount = (idx: number, newAmount: number) => {
        if (!computedPayments) return;
        const updated = [...computedPayments];
        updated[idx] = { ...updated[idx], amount: newAmount };
        setComputedPayments(updated);
    };

    const removePayment = (idx: number) => {
        if (!computedPayments) return;
        setComputedPayments(computedPayments.filter((_, i) => i !== idx));
    };

    const addPayment = () => {
        if (!computedPayments || debts.length === 0) return;
        const firstDebt = debts[0];
        const incomeDate = availableIncomeDates.length > 0 ? availableIncomeDates[0] : new Date().toISOString().slice(0, 10);
        setComputedPayments([
            ...computedPayments,
            {
                debt_id: firstDebt.id,
                debt_name: firstDebt.name,
                amount: 0,
                income_date: incomeDate,
            },
        ]);
    };

    const updatePaymentDebt = (idx: number, debtId: number) => {
        if (!computedPayments) return;
        const debt = debts.find((d) => d.id === debtId);
        if (!debt) return;
        const updated = [...computedPayments];
        updated[idx] = { ...updated[idx], debt_id: debtId, debt_name: debt.name };
        setComputedPayments(updated);
    };

    const updatePaymentDate = (idx: number, incomeDate: string) => {
        if (!computedPayments) return;
        const updated = [...computedPayments];
        updated[idx] = { ...updated[idx], income_date: incomeDate };
        setComputedPayments(updated);
    };

    // --- Per-debt totals ---
    const getDebtTotals = (): { debt: Debt; totalPayments: number; status: 'under' | 'over' | 'exact' }[] => {
        if (!computedPayments) return [];
        const totalsMap: Record<number, number> = {};
        for (const p of computedPayments) {
            totalsMap[p.debt_id] = (totalsMap[p.debt_id] || 0) + p.amount;
        }
        return debts
            .filter((d) => totalsMap[d.id] !== undefined)
            .map((d) => {
                const totalPayments = totalsMap[d.id] || 0;
                const remaining = d.remaining_amount;
                const diff = Math.abs(totalPayments - remaining);
                let status: 'under' | 'over' | 'exact';
                if (diff < 0.01) {
                    status = 'exact';
                } else if (totalPayments < remaining) {
                    status = 'under';
                } else {
                    status = 'over';
                }
                return { debt: d, totalPayments, status };
            });
    };

    const statusColor = (status: 'under' | 'over' | 'exact') => {
        if (status === 'under') return theme.palette.mode === 'dark' ? '#ef5350' : '#c62828';
        if (status === 'over') return theme.palette.mode === 'dark' ? '#ffb74d' : '#e65100';
        return theme.palette.mode === 'dark' ? '#66bb6a' : '#2e7d32';
    };

    const statusLabel = (status: 'under' | 'over' | 'exact') => {
        if (status === 'under') return 'Underpaying';
        if (status === 'over') return 'Overpaying';
        return 'Exact';
    };

    const formatCurrency = (val: number) =>
        val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });

    return (
        <Paper className="section" id="debts" elevation={2} sx={{ p: 0 }}>
            {/* Title Section */}
            <Box sx={{
                backgroundColor: theme.palette.mode === 'dark' ? '#263238' : '#e0e0e0',
                borderRadius: '8px 8px 0 0',
                padding: '15px 20px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
            }}>
                <Typography variant="h4" sx={{ fontWeight: 'bold', m: 0 }}>
                    Debts
                    <HelpIcon text="Track debts and interest rates. Budgie can compute optimal payment plans from your surplus." />
                </Typography>
                <Button
                    variant="contained"
                    color="primary"
                    sx={{ fontWeight: 'bold', px: 3 }}
                    onClick={() => {
                        resetForm();
                        setShowForm(true);
                    }}
                >
                    Add Debt
                </Button>
            </Box>

            {/* Content */}
            <Box sx={{ p: 3 }}>
                {error && (
                    <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>
                )}
                {success && (
                    <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>
                )}

                {/* Inline Form */}
                {showForm && (
                    <Box sx={{
                        backgroundColor: theme.palette.mode === 'dark' ? '#37474f' : '#f5f5f5',
                        borderRadius: '8px',
                        padding: '20px',
                        mb: 3,
                    }}>
                        <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 2 }}>
                            {editingDebtId ? 'Edit' : 'Create'} Debt
                        </Typography>
                        <Grid container spacing={2}>
                            <Grid size={{ xs: 12, sm: 6 }}>
                                <Typography sx={{ color: '#90a4ae', fontSize: 12, fontWeight: 'bold', mb: 1 }}>
                                    Name
                                </Typography>
                                <TextField
                                    placeholder="e.g., Credit Card, Student Loan"
                                    value={form.name}
                                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                                    fullWidth
                                    size="small"
                                />
                            </Grid>
                            <Grid size={{ xs: 12, sm: 6 }}>
                                <Typography sx={{ color: '#90a4ae', fontSize: 12, fontWeight: 'bold', mb: 1 }}>
                                    Total Amount
                                </Typography>
                                <TextField
                                    type="number"
                                    placeholder="0.00"
                                    value={form.total_amount}
                                    onChange={(e) => setForm({ ...form, total_amount: parseFloat(e.target.value) })}
                                    fullWidth
                                    size="small"
                                />
                            </Grid>
                            <Grid size={{ xs: 12, sm: 4 }}>
                                <Typography sx={{ color: '#90a4ae', fontSize: 12, fontWeight: 'bold', mb: 1 }}>
                                    Remaining Amount
                                </Typography>
                                <TextField
                                    type="number"
                                    placeholder="0.00"
                                    value={form.remaining_amount}
                                    onChange={(e) => setForm({ ...form, remaining_amount: parseFloat(e.target.value) })}
                                    fullWidth
                                    size="small"
                                />
                            </Grid>
                            <Grid size={{ xs: 12, sm: 4 }}>
                                <Typography sx={{ color: '#90a4ae', fontSize: 12, fontWeight: 'bold', mb: 1 }}>
                                    Minimum Payment
                                </Typography>
                                <TextField
                                    type="number"
                                    placeholder="0.00"
                                    value={form.min_payment}
                                    onChange={(e) => setForm({ ...form, min_payment: parseFloat(e.target.value) })}
                                    fullWidth
                                    size="small"
                                />
                            </Grid>
                            <Grid size={{ xs: 12, sm: 4 }}>
                                <Typography sx={{ color: '#90a4ae', fontSize: 12, fontWeight: 'bold', mb: 1 }}>
                                    Interest Rate (%)
                                </Typography>
                                <TextField
                                    type="number"
                                    placeholder="0.00"
                                    value={form.interest_rate}
                                    onChange={(e) => setForm({ ...form, interest_rate: parseFloat(e.target.value) })}
                                    fullWidth
                                    size="small"
                                />
                            </Grid>
                            <Grid size={12}>
                                <Box sx={{ display: 'flex', gap: 2, mt: 1 }}>
                                    <Button
                                        variant="contained"
                                        onClick={handleSubmit}
                                        sx={{ fontWeight: 'bold' }}
                                    >
                                        {editingDebtId ? 'Update' : 'Create'} Debt
                                    </Button>
                                    <Button
                                        variant="outlined"
                                        onClick={resetForm}
                                        sx={{ fontWeight: 'bold' }}
                                    >
                                        Cancel
                                    </Button>
                                </Box>
                            </Grid>
                        </Grid>
                    </Box>
                )}

                {/* Debts Table */}
                <TableContainer>
                    <Table size="small">
                        <TableHead>
                            <TableRow>
                                <TableCell sx={{ fontWeight: 'bold' }}>Name</TableCell>
                                <TableCell sx={{ fontWeight: 'bold' }} align="right">Total Amount</TableCell>
                                <TableCell sx={{ fontWeight: 'bold' }} align="right">Remaining</TableCell>
                                <TableCell sx={{ fontWeight: 'bold' }} align="right">Min Payment</TableCell>
                                <TableCell sx={{ fontWeight: 'bold' }} align="right">Interest Rate</TableCell>
                                <TableCell sx={{ fontWeight: 'bold' }} align="center">Actions</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {debts.length === 0 && (
                                <TableRow>
                                    <TableCell colSpan={6} align="center" sx={{ py: 4, color: '#90a4ae' }}>
                                        No debts found. Track loans, credit cards, and other debts here. Budgie can compute optimal payment plans from your budget surplus. Click "Add Debt" above to get started.
                                    </TableCell>
                                </TableRow>
                            )}
                            {debts.map((debt) => (
                                <TableRow key={debt.id}>
                                    <TableCell>{debt.name}</TableCell>
                                    <TableCell align="right">${formatCurrency(debt.total_amount)}</TableCell>
                                    <TableCell align="right">${formatCurrency(debt.remaining_amount)}</TableCell>
                                    <TableCell align="right">${formatCurrency(debt.min_payment)}</TableCell>
                                    <TableCell align="right">{debt.interest_rate}%</TableCell>
                                    <TableCell align="center">
                                        <Button
                                            size="small"
                                            onClick={() => startEdit(debt)}
                                            sx={{ minWidth: 'auto', mr: 1 }}
                                        >
                                            <EditIcon fontSize="small" />
                                        </Button>
                                        <Button
                                            size="small"
                                            color="error"
                                            onClick={() => confirmDelete(debt)}
                                            sx={{ minWidth: 'auto' }}
                                        >
                                            <DeleteIcon fontSize="small" />
                                        </Button>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </TableContainer>

                {/* Compute Payments Section */}
                {debts.length > 0 && (
                    <Box sx={{
                        backgroundColor: theme.palette.mode === 'dark' ? '#37474f' : '#f5f5f5',
                        borderRadius: '8px',
                        padding: '20px',
                        mt: 3,
                    }}>
                        <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 2 }}>
                            Compute Debt Payments
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mb: 2 }}>
                            <Box>
                                <Typography sx={{ color: '#90a4ae', fontSize: 12, fontWeight: 'bold', mb: 1 }}>
                                    Savings Margin
                                </Typography>
                                <TextField
                                    type="number"
                                    placeholder="0.00"
                                    value={savingsMargin}
                                    onChange={(e) => setSavingsMargin(parseFloat(e.target.value))}
                                    size="small"
                                />
                            </Box>
                            <Button
                                variant="contained"
                                onClick={computePayments}
                                sx={{ fontWeight: 'bold', mt: 2.5 }}
                            >
                                Compute Payments
                            </Button>
                        </Box>

                        {computeError && (
                            <Alert severity="error" sx={{ mb: 2 }}>{computeError}</Alert>
                        )}
                        {saveSuccess && (
                            <Alert severity="success" sx={{ mb: 2 }}>{saveSuccess}</Alert>
                        )}

                        {computedPayments && computedPayments.length > 0 && (
                            <Box>
                                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                                    <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                                        Payment Plan
                                    </Typography>
                                    <Button
                                        variant="outlined"
                                        size="small"
                                        startIcon={<AddIcon />}
                                        onClick={addPayment}
                                    >
                                        Add Payment
                                    </Button>
                                </Box>
                                <TableContainer>
                                    <Table size="small">
                                        <TableHead>
                                            <TableRow>
                                                <TableCell sx={{ fontWeight: 'bold' }}>Debt</TableCell>
                                                <TableCell sx={{ fontWeight: 'bold' }} align="right">Amount</TableCell>
                                                <TableCell sx={{ fontWeight: 'bold' }}>Income Date</TableCell>
                                                <TableCell sx={{ fontWeight: 'bold' }} align="center">Actions</TableCell>
                                            </TableRow>
                                        </TableHead>
                                        <TableBody>
                                            {computedPayments.map((payment, idx) => (
                                                <TableRow key={`payment-${idx}`}>
                                                    <TableCell>
                                                        <Select
                                                            value={payment.debt_id}
                                                            onChange={(e) => updatePaymentDebt(idx, e.target.value as number)}
                                                            size="small"
                                                            sx={{ minWidth: 140 }}
                                                        >
                                                            {debts.map((d) => (
                                                                <MenuItem key={d.id} value={d.id}>{d.name}</MenuItem>
                                                            ))}
                                                        </Select>
                                                    </TableCell>
                                                    <TableCell align="right">
                                                        <TextField
                                                            type="number"
                                                            value={payment.amount}
                                                            onChange={(e) => updatePaymentAmount(idx, parseFloat(e.target.value) || 0)}
                                                            size="small"
                                                            sx={{ width: 120 }}
                                                            slotProps={{ input: { sx: { textAlign: 'right' } } }}
                                                        />
                                                    </TableCell>
                                                    <TableCell>
                                                        {availableIncomeDates.length > 0 ? (
                                                            <Select
                                                                value={payment.income_date}
                                                                onChange={(e) => updatePaymentDate(idx, e.target.value as string)}
                                                                size="small"
                                                                sx={{ minWidth: 140 }}
                                                            >
                                                                {availableIncomeDates.map((d) => (
                                                                    <MenuItem key={d} value={d}>{d}</MenuItem>
                                                                ))}
                                                            </Select>
                                                        ) : (
                                                            <TextField
                                                                type="date"
                                                                value={payment.income_date}
                                                                onChange={(e) => updatePaymentDate(idx, e.target.value)}
                                                                size="small"
                                                                sx={{ minWidth: 140 }}
                                                            />
                                                        )}
                                                    </TableCell>
                                                    <TableCell align="center">
                                                        <IconButton
                                                            size="small"
                                                            color="error"
                                                            onClick={() => removePayment(idx)}
                                                        >
                                                            <DeleteIcon fontSize="small" />
                                                        </IconButton>
                                                    </TableCell>
                                                </TableRow>
                                            ))}
                                        </TableBody>
                                    </Table>
                                </TableContainer>

                                {/* Per-debt totals with color coding */}
                                <Box sx={{
                                    mt: 2,
                                    p: 2,
                                    backgroundColor: theme.palette.mode === 'dark' ? '#263238' : '#e8e8e8',
                                    borderRadius: '8px',
                                }}>
                                    <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
                                        Payment Summary
                                    </Typography>
                                    {getDebtTotals().map(({ debt, totalPayments, status }) => (
                                        <Box
                                            key={debt.id}
                                            sx={{
                                                display: 'flex',
                                                justifyContent: 'space-between',
                                                alignItems: 'center',
                                                py: 0.5,
                                                px: 1,
                                                borderLeft: `4px solid ${statusColor(status)}`,
                                                mb: 0.5,
                                                borderRadius: '0 4px 4px 0',
                                                backgroundColor: theme.palette.mode === 'dark' ? '#37474f' : '#f5f5f5',
                                            }}
                                        >
                                            <Typography sx={{ fontWeight: 'bold', fontSize: 13 }}>
                                                {debt.name}
                                            </Typography>
                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                                <Typography sx={{ fontSize: 13 }}>
                                                    ${formatCurrency(totalPayments)} / ${formatCurrency(debt.remaining_amount)}
                                                </Typography>
                                                <Typography sx={{
                                                    fontSize: 12,
                                                    fontWeight: 'bold',
                                                    color: statusColor(status),
                                                }}>
                                                    {statusLabel(status)}
                                                    {status === 'under' && ` (-$${formatCurrency(debt.remaining_amount - totalPayments)})`}
                                                    {status === 'over' && ` (+$${formatCurrency(totalPayments - debt.remaining_amount)})`}
                                                </Typography>
                                            </Box>
                                        </Box>
                                    ))}
                                </Box>

                                <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
                                    <Button
                                        variant="contained"
                                        color="primary"
                                        onClick={savePayments}
                                        sx={{ fontWeight: 'bold' }}
                                    >
                                        Save Payments
                                    </Button>
                                    <Button
                                        variant="outlined"
                                        onClick={() => setComputedPayments(null)}
                                        sx={{ fontWeight: 'bold' }}
                                    >
                                        Discard
                                    </Button>
                                </Box>
                            </Box>
                        )}

                        {computedPayments && computedPayments.length === 0 && (
                            <Alert severity="info">No payments computed. Check your debts and savings margin.</Alert>
                        )}
                    </Box>
                )}
            </Box>

            {/* Delete Confirmation Dialog */}
            <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
                <DialogTitle>Delete Debt</DialogTitle>
                <DialogContent>
                    <DialogContentText>
                        Are you sure you want to delete "{debtToDelete?.name}"? This action cannot be undone.
                    </DialogContentText>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
                    <Button onClick={handleDelete} color="error" variant="contained">
                        Delete
                    </Button>
                </DialogActions>
            </Dialog>
        </Paper>
    );
}
