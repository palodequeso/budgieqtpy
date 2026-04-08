import {
    Button,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    FormControl,
    InputLabel,
    MenuItem,
    Select,
    Typography,
} from '@mui/material';
import * as React from 'react';
import { api } from './renderUtils';

interface CalendarGotPaidProps {
    open: boolean;
    close: (saved?: boolean) => void;
    profile: any;
    schedule: any;
}

export default function CalendarGotPaid({
    open,
    close,
    profile,
    schedule,
}: CalendarGotPaidProps) {
    const [selectedDate, setSelectedDate] = React.useState('');
    const [selectedAccount, setSelectedAccount] = React.useState('');
    const [unpaidIncomeDates, setUnpaidIncomeDates] = React.useState<string[]>([]);

    React.useEffect(() => {
        if (open && schedule?.sorted_income_dates) {
            // Filter to only show dates where income hasn't been marked as paid
            const unpaid: string[] = [];
            
            for (const dateStr of schedule.sorted_income_dates) {
                const column = schedule.columns?.[dateStr];
                if (column?.incomes && column.incomes.length > 0) {
                    const incomeEntry = column.incomes[0];
                    // Check if all items in the income entry are paid
                    const allPaid = incomeEntry.items?.every((item: any) => item.ledger_entry !== null);
                    if (!allPaid) {
                        unpaid.push(dateStr);
                    }
                }
            }
            
            setUnpaidIncomeDates(unpaid);
            if (unpaid.length > 0) {
                setSelectedDate(unpaid[0]);
            }
        }
    }, [open, schedule]);

    React.useEffect(() => {
        if (profile?.accounts && profile.accounts.length > 0) {
            setSelectedAccount(profile.accounts[0].id.toString());
        }
    }, [profile]);

    const handleSave = async () => {
        try {
            if (!selectedDate || !selectedAccount) {
                alert('Please select both a date and an account');
                return;
            }

            const column = schedule.columns[selectedDate];
            if (!column?.incomes || column.incomes.length === 0) {
                alert('No income entry found for this date');
                return;
            }

            const incomeEntry = column.incomes[0];
            const incomeItem = incomeEntry.items[0];
            
            // Create ledger entry for the income
            await api.post('/ledger', {
                profile_id: profile.id,
                extrapolation_item_id: incomeItem.extrapolation_item.id,
                account_id: parseInt(selectedAccount),
                amount: incomeEntry.total(),
                paid_date: new Date().toISOString().split('T')[0],
                income_date: selectedDate,
                type: 'income',
            });

            close(true);
        } catch (error) {
            console.error('Failed to mark income as paid:', error);
            alert('Failed to mark income as paid');
        }
    };

    if (unpaidIncomeDates.length === 0 && open) {
        return (
            <Dialog open={open} onClose={() => close(false)} maxWidth="sm" fullWidth>
                <DialogTitle>I Got Paid</DialogTitle>
                <DialogContent>
                    <Typography>All income dates have already been marked as paid!</Typography>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => close(false)} color="primary">
                        Close
                    </Button>
                </DialogActions>
            </Dialog>
        );
    }

    return (
        <Dialog open={open} onClose={() => close(false)} maxWidth="sm" fullWidth>
            <DialogTitle>Hooray, it's payday! 🎉</DialogTitle>
            <DialogContent>
                <FormControl fullWidth margin="normal">
                    <InputLabel>Income Date</InputLabel>
                    <Select
                        value={selectedDate}
                        label="Income Date"
                        onChange={(e) => setSelectedDate(e.target.value)}
                    >
                        {unpaidIncomeDates.map((date) => (
                            <MenuItem key={date} value={date}>
                                {date}
                            </MenuItem>
                        ))}
                    </Select>
                </FormControl>

                <FormControl fullWidth margin="normal">
                    <InputLabel>Account</InputLabel>
                    <Select
                        value={selectedAccount}
                        label="Account"
                        onChange={(e) => setSelectedAccount(e.target.value)}
                    >
                        {profile?.accounts?.map((account: any) => (
                            <MenuItem key={account.id} value={account.id.toString()}>
                                {account.name}
                            </MenuItem>
                        ))}
                    </Select>
                </FormControl>
            </DialogContent>
            <DialogActions>
                <Button onClick={() => close(false)} color="secondary">
                    Cancel
                </Button>
                <Button onClick={handleSave} color="primary" variant="contained">
                    Mark as Paid
                </Button>
            </DialogActions>
        </Dialog>
    );
}
