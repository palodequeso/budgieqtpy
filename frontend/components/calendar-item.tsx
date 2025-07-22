import {
    Alert,
    Button,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    List,
    ListItemButton,
    ListItemText,
    MenuItem,
    Paper,
    Select,
    TextField
} from '@mui/material';
import { LocalizationProvider } from '@mui/x-date-pickers';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { DesktopDatePicker } from '@mui/x-date-pickers/DesktopDatePicker';
import * as React from 'react';
import { CalendarEntry } from './calendar-extrapolation';
import CurrencyLabel from './currency-label';
import DateLabel from './date-label';
import { api } from './renderUtils';

export default function CalendarItem({ entry, profile, close }: { entry: CalendarEntry, profile: any, close: any }) {
    const [fetchError, setFetchError] = React.useState('');
    const [selectedAccount, setSelectedAccount] = React.useState(0);
    const [selectedItemIndex, setSelectedItemIndex] = React.useState(0);

    async function save(item) {
        try {
            const updateItemResult = await api.put(`/extrapolate/updateitem/${item.id}`, {
                amount: parseFloat(item.amount.toString()),
                date: item.date,
            });
            close(true);
            // TODO: Should this stay open? Or should it close?
        } catch (e) {
            setFetchError(e.message);
        }
    }

    async function markPaid(item) {
        try {
            if (!selectedAccount) {
                throw new Error('Please select an account');
            }

            const result = await api.post(`/budget/markpaid/${profile.id}`, {
                extrapolationItemId: item.id,
                accountId: selectedAccount,
            });
            entry.items[selectedItemIndex].ledgerEntry = (result as any).ledgerEntry;
            item.ledgerEntry = (result as any).ledgerEntry;
            close(true);
            // TODO: Should this stay open? Or should it close?
        } catch (e) {
            setFetchError(e.message);
        }
    }

    return (
        entry !== null ? (
            <Dialog open={entry !== null} onClose={close} maxWidth="md" fullWidth>
                <DialogTitle>Edit Calendar Cell</DialogTitle>
                <DialogContent>
                    <LocalizationProvider dateAdapter={AdapterDateFns}>
                        {fetchError && <Alert severity="error">{fetchError}</Alert>}
                        <Paper className="item-breakdown-container" elevation={4}>
                            <h4>Scheduled Expenses for this Entry</h4>
                            <List>
                                {entry.items.map((item, itemIndex) => <ListItemButton
                                    key={item.id}
                                    selected={selectedItemIndex === itemIndex}
                                    className="item-breakdown-item"
                                    onClick={() => setSelectedItemIndex(itemIndex)}
                                >
                                    <ListItemText>
                                        <DateLabel date={item.date} />
                                    </ListItemText>
                                    <ListItemText>
                                        <CurrencyLabel amount={parseFloat(item.amount.toString())} />
                                    </ListItemText>
                                    {item.ledgerEntry && item.ledgerEntry.id !== null ? (
                                        <ListItemText>
                                            <i className="material-icons">
                                                check_circle
                                            </i>
                                            <ListItemText>
                                                Paid
                                            </ListItemText>
                                        </ListItemText>
                                    ) : (
                                        <ListItemText>
                                            <i className="material-icons">
                                                uncheck_circle
                                            </i>
                                            <ListItemText>
                                                Unpaid
                                            </ListItemText>
                                        </ListItemText>)}
                                </ListItemButton>)}
                            </List>
                        </Paper>
                        {selectedItemIndex !== -1 ? (<div className="selected-breakdown-item-form">
                            <Paper className="mark-paid-container" elevation={4}>
                                <h5>Mark Item as Paid</h5>
                                <div className="form-field">
                                    <Select
                                        id="edit-calendar-cell-account"
                                        label="Account"
                                        value={selectedAccount}
                                        onChange={(e) => {
                                            setSelectedAccount(parseInt(e.target.value.toString(), 10));
                                        }}
                                    >
                                        <MenuItem value={0}>Select Account</MenuItem>
                                        {profile
                                            ? profile.accounts.map((account) => {
                                                return (
                                                    <MenuItem
                                                        key={account.id}
                                                        value={account.id}
                                                    >
                                                        {account.name}
                                                    </MenuItem>
                                                );
                                            })
                                            : null}
                                    </Select>
                                </div>
                                <div className="form-field">
                                    <Button
                                        id="mark-paid-with-ledger"
                                        variant="contained"
                                        color="primary"
                                        disabled={
                                            !entry.items[selectedItemIndex] ||
                                            entry.items[selectedItemIndex].ledgerEntry !== null ||
                                            selectedAccount === 0
                                        }
                                        onClick={async () => {
                                            markPaid(entry.items[selectedItemIndex]);
                                        }}
                                    >
                                        Mark Paid with Ledger Entry
                                    </Button>
                                </div>
                            </Paper>
                            <Paper elevation={4} className="mark-paid-container">
                                <h5>Modify the Item Directly</h5>
                                <h6>NOT IMPLEMENTED YET, MIGHT MOVE CONTROLS TO ABOVE</h6>
                                <div className='form-field'>
                                    <TextField
                                        autoFocus
                                        id="edit-calendar-cell-amount"
                                        label="Amount"
                                        type="text"
                                        fullWidth
                                        variant="standard"
                                        onChange={(e) => {
                                            entry.items[selectedItemIndex].amount = parseFloat(e.target.value.toString());
                                        }}
                                        defaultValue={parseFloat(entry.items[selectedItemIndex].amount.toString()).toFixed(2)}
                                    />
                                </div>
                                <div className="form-field">
                                    <DesktopDatePicker
                                        label="Start Date"
                                        // inputFormat="MM/dd/yyyy"
                                        value={entry.items[selectedItemIndex].date}
                                        onChange={(value) => {
                                            entry.items[selectedItemIndex].date = value as Date;
                                        }}
                                        // renderInput={(params) => (
                                        //     <TextField {...params} />
                                        // )}
                                    />
                                </div>
                                <div className="form-field">
                                    <Button variant="contained" onClick={() => save(entry.items[selectedItemIndex])}>
                                        Save
                                    </Button>
                                </div>
                                <label>
                                    Normally this is only done if scheduled expense has changed after it was previously scheduled, if you're just paying it early, there's no need to do this.
                                </label>
                            </Paper>
                        </div>) : null}
                    </LocalizationProvider>
                </DialogContent>
                <DialogActions>
                    <Button variant="outlined" onClick={close}>
                        Cancel
                    </Button>
                </DialogActions>
            </Dialog>
        ) : null
    );
}
