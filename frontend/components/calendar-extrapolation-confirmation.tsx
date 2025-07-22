import {
    Button,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle
} from '@mui/material';
import * as React from 'react';

export default function CalendarExtrapolationConfirmation({
    open,
    close,
    extrapolate,
}) {
    return (
        <Dialog open={open} onClose={close} maxWidth="md" fullWidth>
            <DialogTitle>Budget Extrapolation Confirmation</DialogTitle>
            <DialogContent>
                Budget extrapolation is meant to be used when you are initially done setting up budget items. It will
                take this data and attempt to schedule a budget for the start and end time periods you set in the controls.
                <br/>
                Basically it first fills out all incomes as columns in a schedule spreadsheet. Then it fills out all
                expenses finding the first available column that has enough money to cover the expense. If there is not
                enough money in the schedule, it will mark it as unscheduled and you can manually slot those entries in.
                <br/>
                After this, you should have a servicable budget that you can start marking entries off as you pay.
                <br/>
                It is also reccomended that once your base schedule is set, you try to fit in some savings items to build up
                some emergency fund as well, but this app is just a helper. It is up to you to make the right choices for you.
                <br/>
                Thinking about money is pain for many of us, and this tool attempts to make it a little easier.
                <br/>
                Good luck out there!
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
