import {
    Alert,
    Button,
    Card,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    MenuItem,
    Select,
    Typography
} from '@mui/material';
import * as React from 'react';
import { api } from './renderUtils';

export default function CalendarUnscheduled({
    open,
    sortedIncomeDates,
    unscheduled,
    profile,
    close,
}) {
    const [saveError, setSaveError] = React.useState('');

    async function save() {
        try {
            if (unscheduled.filter((u) => u.incomeDate === null).length > 0) {
                setSaveError('Please select an income date for all items.');
                return;
            }

            // Map to the shape the API expects: { id, income_date }
            const payload = unscheduled.map((u) => ({
                id: u.id,
                income_date: u.incomeDate,
            }));

            await api.post(
                `/calendar/${profile.id}/fixunscheduled`,
                payload,
            );
            close(true);
        } catch (e) {
            setSaveError(e.message);
        }
    }

    return (
        <Dialog open={open} onClose={close} maxWidth="md" fullWidth>
            <DialogTitle>Unscheduled Expenses</DialogTitle>
            <DialogContent>
                {saveError !== '' && (
                    <Alert severity="error">{saveError}</Alert>
                )}
                {unscheduled.map((item) => (
                    <Card
                        key={item.id}
                        sx={{
                            display: 'inline-flex',
                            flexDirection: 'column',
                            padding: '1rem',
                            margin: '1rem',
                            minWidth: '260px',
                            maxWidth: '320px',
                        }}
                    >
                        <Typography>Name: {item.budgetItem.name}</Typography>
                        <Typography>
                            Due: {item.date.substring(0, 10)}
                        </Typography>
                        <Typography>Amt: -${item.amount}</Typography>
                        <div>
                            <Select
                                id="extrapolation-item-income-date"
                                label="Income Date"
                                variant="outlined"
                                fullWidth
                                defaultValue="0"
                                onChange={(e) => {
                                    item.incomeDate = e.target.value;
                                }}
                            >
                                <MenuItem value="0">
                                    Select Income Date
                                </MenuItem>
                                {sortedIncomeDates.map((date) => (
                                    <MenuItem key={date} value={date}>
                                        {date}
                                    </MenuItem>
                                ))}
                            </Select>
                        </div>
                    </Card>
                ))}
            </DialogContent>
            <DialogActions>
                <Button variant="outlined" color="secondary" onClick={close}>
                    Cancel
                </Button>
                <Button onClick={save} variant="contained" color="primary">
                    Save
                </Button>
            </DialogActions>
        </Dialog>
    );
}
