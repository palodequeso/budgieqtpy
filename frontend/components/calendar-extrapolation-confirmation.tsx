import {
    Box,
    Button,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    Typography
} from '@mui/material';
import * as React from 'react';

export default function CalendarExtrapolationConfirmation({
    open,
    close,
    extrapolate,
}) {
    return (
        <Dialog open={open} onClose={close} maxWidth="md" fullWidth>
            <DialogTitle>Run Budget Extrapolation?</DialogTitle>
            <DialogContent>
                <Typography variant="body1" gutterBottom>
                    Extrapolation schedules your recurring budget items across the date range
                    you've selected. Here's how it works:
                </Typography>
                <Box component="ul" sx={{ pl: 2, my: 1 }}>
                    <li>
                        <Typography variant="body2">
                            Your income items become columns in the schedule — one column per payday
                        </Typography>
                    </li>
                    <li>
                        <Typography variant="body2">
                            Expenses are placed into the earliest column that can cover them
                        </Typography>
                    </li>
                    <li>
                        <Typography variant="body2">
                            If an expense can't fit anywhere, it's marked as unscheduled for you to handle manually
                        </Typography>
                    </li>
                    <li>
                        <Typography variant="body2">
                            Items you've already marked as paid are preserved
                        </Typography>
                    </li>
                </Box>
                <Typography variant="body1" gutterBottom sx={{ mt: 1 }}>
                    After extrapolation, take a moment to review the results. The scheduling
                    algorithm does its best, but you know your finances better than any algorithm.
                </Typography>
                <Typography variant="body1" gutterBottom>
                    Once your schedule looks right, consider adding savings items to start
                    building a safety net — even small amounts add up.
                </Typography>
                <Typography variant="body1" sx={{ mt: 1 }}>
                    You've got this!
                </Typography>
            </DialogContent>
            <DialogActions>
                <Button variant="outlined" color="secondary" onClick={close}>
                    Cancel
                </Button>
                <Button onClick={() => {
                    close();
                    extrapolate();
                }} variant="contained" color="primary">
                    Extrapolate
                </Button>
            </DialogActions>
        </Dialog>
    );
}
