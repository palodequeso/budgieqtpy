import {
    Alert,
    Button,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    Box,
    MenuItem,
    Select,
    TextField,
    Typography,
} from '@mui/material';
import * as React from 'react';
import { CalendarEntry } from './calendar-extrapolation';
import CurrencyLabel from './currency-label';
import DateLabel from './date-label';
import MarkPaidDialog from './mark-paid-dialog';
import { api } from './renderUtils';

export default function CalendarItem({ entry, profile, close, schedule }: { entry: CalendarEntry, profile: any, close: any, schedule?: any }) {
    const [markPaidDialogOpen, setMarkPaidDialogOpen] = React.useState(false);
    const [selectedItem, setSelectedItem] = React.useState(null);
    const [moveDialogOpen, setMoveDialogOpen] = React.useState(false);
    const [moveItem, setMoveItem] = React.useState<any>(null);
    const [moveTarget, setMoveTarget] = React.useState('');
    const [splitDialogOpen, setSplitDialogOpen] = React.useState(false);
    const [splitItem, setSplitItem] = React.useState<any>(null);
    const [splitKeepAmount, setSplitKeepAmount] = React.useState('');
    const [splitTarget, setSplitTarget] = React.useState('');
    const [error, setError] = React.useState('');

    const sortedDates: string[] = schedule?.sorted_income_dates ?? [];

    function handleMarkPaidClick(item) {
        setSelectedItem(item);
        setMarkPaidDialogOpen(true);
    }

    function handleMarkPaidClose(refresh?: boolean) {
        setMarkPaidDialogOpen(false);
        setSelectedItem(null);
        if (refresh) {
            close(true);
        }
    }

    function openMoveDialog(item: any) {
        setMoveItem(item);
        setMoveTarget('');
        setError('');
        setMoveDialogOpen(true);
    }

    async function handleMove() {
        if (!moveItem || !moveTarget || !profile) return;
        try {
            await api.post(`/calendar/${profile.id}/move_item`, {
                budget_item_id: moveItem.extrapolation_item?.budget_item_id ?? entry.budget_item?.id,
                from_income_date: entry.income_date,
                to_income_date: moveTarget,
            });
            setMoveDialogOpen(false);
            setMoveItem(null);
            close(true);
        } catch (e: any) {
            setError(e.message);
        }
    }

    function openSplitDialog(item: any) {
        setSplitItem(item);
        const amt = Math.abs(item.extrapolation_item?.amount ?? item.amount ?? 0);
        setSplitKeepAmount(Math.floor(amt * 0.5).toString());
        setSplitTarget(entry.income_date || '');
        setError('');
        setSplitDialogOpen(true);
    }

    async function handleSplit() {
        if (!splitItem || !profile) return;
        const keep = parseFloat(splitKeepAmount);
        if (isNaN(keep) || keep <= 0) {
            setError('Enter a valid amount');
            return;
        }
        const total = Math.abs(splitItem.extrapolation_item?.amount ?? splitItem.amount ?? 0);
        if (keep >= total) {
            setError('Amount must be less than the total');
            return;
        }
        try {
            await api.post(`/calendar/${profile.id}/split_item`, {
                extrapolation_item_id: splitItem.extrapolation_item?.id ?? splitItem.id,
                keep_amount: keep,
                remainder_income_date: splitTarget || null,
            });
            setSplitDialogOpen(false);
            setSplitItem(null);
            close(true);
        } catch (e: any) {
            setError(e.message);
        }
    }

    if (!entry) {
        return null;
    }

    const fmt = (n: number) => n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });

    return (
        <>
            <Dialog open={entry !== null} onClose={close} maxWidth="sm" fullWidth>
                <DialogTitle>
                    Schedule Entry - {entry.budget_item?.name}
                </DialogTitle>
                <DialogContent>
                    {/* Entry Summary */}
                    <Box sx={{
                        bgcolor: 'background.paper',
                        p: 2,
                        borderRadius: 1,
                        mb: 2,
                        border: 1,
                        borderColor: 'divider'
                    }}>
                        <Typography variant="h6" gutterBottom>
                            {entry.budget_item?.name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            Type: {entry.budget_item?.type}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            Budget Item Amount: <CurrencyLabel amount={entry.budget_item?.amount ?? 0} />
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            Income Date: {entry.income_date ? new Date(entry.income_date).toLocaleDateString() : 'N/A'}
                        </Typography>
                        <Typography variant="body2" color="primary" fontWeight="bold">
                            Entry Total: <CurrencyLabel amount={entry.items.reduce((sum, item) => sum + (item.extrapolation_item?.amount ?? item.amount ?? 0), 0)} />
                        </Typography>
                    </Box>

                    {/* Items Header */}
                    <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                        Scheduled Items ({entry.items.length} item{entry.items.length !== 1 ? 's' : ''})
                    </Typography>

                    {/* Items List */}
                    <Box sx={{ mt: 2 }}>
                        {entry.items.map((item, idx) => {
                            const isPaid = item.ledger_entry && item.ledger_entry.id !== null;
                            const itemAmount = item.extrapolation_item?.amount ?? item.amount ?? 0;
                            return (
                                <Box
                                    key={item.id || idx}
                                    sx={{
                                        bgcolor: 'background.paper',
                                        p: 1.5,
                                        mb: 1,
                                        borderRadius: 1,
                                        border: 1,
                                        borderColor: 'divider',
                                    }}
                                >
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: isPaid ? 0 : 1 }}>
                                        {entry.items.length > 1 && (
                                            <Typography variant="body2" fontWeight="bold" sx={{ minWidth: 30 }}>
                                                #{idx + 1}
                                            </Typography>
                                        )}
                                        {item.extrapolation_item?.name && (
                                            <Typography variant="body2" fontWeight="bold">
                                                {item.extrapolation_item.name}
                                            </Typography>
                                        )}
                                        <Box sx={{ minWidth: 110 }}>
                                            <Typography variant="body2" color="text.secondary">
                                                <DateLabel date={item.extrapolation_item?.date || item.date} />
                                            </Typography>
                                        </Box>
                                        <Typography variant="body2" fontWeight="bold">
                                            <CurrencyLabel amount={parseFloat(itemAmount.toString())} />
                                        </Typography>
                                        <Box sx={{ flexGrow: 1 }} />
                                        {isPaid && (
                                            <Typography variant="body2" color="success.main" fontWeight="bold">
                                                Paid
                                            </Typography>
                                        )}
                                    </Box>
                                    {/* Action buttons for unpaid items */}
                                    {!isPaid && (
                                        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                                            <Button size="small" variant="contained" onClick={() => handleMarkPaidClick(item)}>
                                                Mark Paid
                                            </Button>
                                            <Button size="small" variant="outlined" onClick={() => openMoveDialog(item)}>
                                                Move
                                            </Button>
                                            <Button size="small" variant="outlined" onClick={() => openSplitDialog(item)}>
                                                Split
                                            </Button>
                                        </Box>
                                    )}
                                </Box>
                            );
                        })}
                    </Box>
                </DialogContent>
                <DialogActions sx={{ p: 2, bgcolor: 'background.paper' }}>
                    <Button
                        variant="contained"
                        onClick={() => close(false)}
                        sx={{ bgcolor: 'grey.600', color: 'white', '&:hover': { bgcolor: 'grey.700' } }}
                    >
                        Close
                    </Button>
                </DialogActions>
            </Dialog>

            {/* Mark Paid Dialog */}
            <MarkPaidDialog
                open={markPaidDialogOpen}
                item={selectedItem}
                entry={entry}
                profile={profile}
                onClose={handleMarkPaidClose}
            />

            {/* Move Dialog */}
            <Dialog open={moveDialogOpen} onClose={() => setMoveDialogOpen(false)} maxWidth="xs" fullWidth>
                <DialogTitle>Move Item</DialogTitle>
                <DialogContent>
                    {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
                    <Typography variant="body2" sx={{ mb: 2 }}>
                        Move to which pay period?
                    </Typography>
                    <Select
                        value={moveTarget}
                        onChange={(e) => setMoveTarget(e.target.value)}
                        fullWidth
                        displayEmpty
                    >
                        <MenuItem value="" disabled>Select destination...</MenuItem>
                        {sortedDates
                            .filter((d) => d !== entry.income_date)
                            .map((d) => (
                                <MenuItem key={d} value={d}>{d}</MenuItem>
                            ))}
                    </Select>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setMoveDialogOpen(false)}>Cancel</Button>
                    <Button variant="contained" onClick={handleMove} disabled={!moveTarget}>Move</Button>
                </DialogActions>
            </Dialog>

            {/* Split Dialog */}
            <Dialog open={splitDialogOpen} onClose={() => setSplitDialogOpen(false)} maxWidth="xs" fullWidth>
                <DialogTitle>Split Item</DialogTitle>
                <DialogContent>
                    {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
                    {splitItem && (
                        <>
                            <Typography variant="body2" sx={{ mb: 1 }}>
                                Total: ${fmt(Math.abs(splitItem.extrapolation_item?.amount ?? splitItem.amount ?? 0))}
                            </Typography>
                            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                                How much to keep in this pay period?
                            </Typography>
                            <TextField
                                label="Keep amount"
                                type="number"
                                fullWidth
                                value={splitKeepAmount}
                                onChange={(e) => setSplitKeepAmount(e.target.value)}
                                sx={{ mb: 2 }}
                                inputProps={{ step: 0.01, min: 0.01 }}
                            />
                            {splitKeepAmount && !isNaN(parseFloat(splitKeepAmount)) && (
                                <Typography variant="body2" sx={{ mb: 2 }}>
                                    Remainder: ${fmt(Math.abs(splitItem.extrapolation_item?.amount ?? splitItem.amount ?? 0) - parseFloat(splitKeepAmount))}
                                </Typography>
                            )}
                            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                                Move remainder to:
                            </Typography>
                            <Select
                                value={splitTarget}
                                onChange={(e) => setSplitTarget(e.target.value)}
                                fullWidth
                                displayEmpty
                            >
                                <MenuItem value={entry.income_date || ''}>Same column (keep here)</MenuItem>
                                {sortedDates
                                    .filter((d) => d !== entry.income_date)
                                    .map((d) => (
                                        <MenuItem key={d} value={d}>{d}</MenuItem>
                                    ))}
                            </Select>
                        </>
                    )}
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setSplitDialogOpen(false)}>Cancel</Button>
                    <Button variant="contained" onClick={handleSplit}>Split</Button>
                </DialogActions>
            </Dialog>
        </>
    );
}
