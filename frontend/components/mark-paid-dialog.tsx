import {
    Alert,
    Button,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    FormControl,
    InputLabel,
    MenuItem,
    Select,
    TextField,
    Typography,
    Box
} from '@mui/material';
import { LocalizationProvider } from '@mui/x-date-pickers';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { DesktopDatePicker } from '@mui/x-date-pickers/DesktopDatePicker';
import * as React from 'react';
import { api } from './renderUtils';

interface MarkPaidDialogProps {
    open: boolean;
    item: any;
    entry: any;
    profile: any;
    onClose: (refresh?: boolean) => void;
}

export default function MarkPaidDialog({ open, item, entry, profile, onClose }: MarkPaidDialogProps) {
    const [selectedAccount, setSelectedAccount] = React.useState(0);
    const [paidAmount, setPaidAmount] = React.useState(item?.amount ?? 0);
    const [paidDate, setPaidDate] = React.useState(new Date());
    const [fetchError, setFetchError] = React.useState('');

    // Reset form when item changes
    React.useEffect(() => {
        if (item) {
            setPaidAmount(item.extrapolation_item?.amount ?? item.amount ?? 0);
            setPaidDate(new Date());
            setSelectedAccount(0);
            setFetchError('');
        }
    }, [item]);

    async function handleMarkPaid() {
        try {
            if (!selectedAccount) {
                setFetchError('Please select an account');
                return;
            }

            await api.post(`/budget/markpaid/${profile.id}`, {
                extrapolationItemId: item.extrapolation_item?.id ?? item.id,
                accountId: selectedAccount,
            });

            onClose(true); // Close with refresh flag
        } catch (e) {
            setFetchError(e.message);
        }
    }

    if (!item || !entry) {
        return null;
    }

    return (
        <Dialog open={open} onClose={() => onClose(false)} maxWidth="sm" fullWidth>
            <DialogTitle>💳 Mark as Paid</DialogTitle>
            <DialogContent>
                <LocalizationProvider dateAdapter={AdapterDateFns}>
                    {fetchError && <Alert severity="error" sx={{ mb: 2 }}>{fetchError}</Alert>}
                    
                    {/* Item Info */}
                    <Box sx={{ 
                        bgcolor: 'background.paper', 
                        p: 2, 
                        borderRadius: 1, 
                        mb: 3,
                        border: 1,
                        borderColor: 'divider'
                    }}>
                        <Typography variant="h6" gutterBottom>
                            {entry.budget_item?.name ?? entry.budgetItem?.name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            Type: {entry.budget_item?.type ?? entry.budgetItem?.type}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            Income Date: {entry.income_date ? new Date(entry.income_date).toLocaleDateString() : (entry.incomeDate ? new Date(entry.incomeDate).toLocaleDateString() : 'N/A')}
                        </Typography>
                        <Typography variant="body2" color="primary" fontWeight="bold">
                            Due Date: {item.extrapolation_item?.date ? new Date(item.extrapolation_item.date).toLocaleDateString() : (item.date ? new Date(item.date).toLocaleDateString() : 'N/A')}
                        </Typography>
                    </Box>

                    {/* Account Selection */}
                    <FormControl fullWidth sx={{ mb: 2 }}>
                        <InputLabel id="account-select-label">Account</InputLabel>
                        <Select
                            labelId="account-select-label"
                            id="account-select"
                            value={selectedAccount}
                            label="Account"
                            onChange={(e) => setSelectedAccount(Number(e.target.value))}
                        >
                            <MenuItem value={0}>Select Account</MenuItem>
                            {profile?.accounts?.map((account) => (
                                <MenuItem key={account.id} value={account.id}>
                                    {account.name}
                                </MenuItem>
                            ))}
                        </Select>
                    </FormControl>

                    {/* Amount */}
                    <TextField
                        fullWidth
                        label="Actual Paid Amount"
                        type="number"
                        value={paidAmount}
                        onChange={(e) => setPaidAmount(parseFloat(e.target.value))}
                        sx={{ mb: 2 }}
                        inputProps={{ step: 0.01 }}
                    />

                    {/* Date */}
                    <DesktopDatePicker
                        label="Actual Paid Date"
                        value={paidDate}
                        onChange={(value) => setPaidDate(value as Date)}
                        slotProps={{
                            textField: {
                                fullWidth: true,
                            }
                        }}
                    />
                </LocalizationProvider>
            </DialogContent>
            <DialogActions>
                <Button onClick={() => onClose(false)} variant="outlined">
                    ❌ Cancel
                </Button>
                <Button 
                    onClick={handleMarkPaid} 
                    variant="contained" 
                    color="primary"
                    disabled={selectedAccount === 0}
                >
                    ✅ Save Payment
                </Button>
            </DialogActions>
        </Dialog>
    );
}
