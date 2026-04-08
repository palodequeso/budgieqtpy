import {
    Alert,
    Dialog,
    DialogTitle,
    DialogContent,
    Paper,
    TextField,
    Select,
    MenuItem,
    FormGroup,
    FormControlLabel,
    Switch,
    DialogActions,
    Button,
    Grid,
} from '@mui/material';
import * as React from 'react';
import { api } from './renderUtils';

export default function CalendarOneOff({ sortedIncomeDates, open, profile, close }) {
    const [account, setAccount] = React.useState(
        profile?.accounts?.length > 0 ? profile.accounts[0].id : 0,
    );
    const [name, setName] = React.useState('');
    const [amount, setAmount] = React.useState(0);
    const [incomeDate, setIncomeDate] = React.useState('none');
    const [type, setType] = React.useState('expense');
    const [addingOneOffExpensePaid, setAddingOneOffExpensePaid] =
        React.useState(false);
    const [saveError, setSaveError] = React.useState('');

    async function save() {
        try {
            const oneOffData = {
                account,
                amount,
                name,
                incomeDate,
                type,
                addingOneOffExpensePaid,
            };
            await api.post(`/calendar/${profile.id}/oneoff`, oneOffData);
            close(true);
        } catch (err) {
            setSaveError(err.message);
        }
    }

    return (
        <Dialog open={open} onClose={close} maxWidth="md" fullWidth>
            <DialogTitle>Edit Calendar Cell</DialogTitle>
            <DialogContent>
                <Paper>
                    <h4>Add Extrapolation/Budget Item</h4>
                    {saveError && <Alert severity="error" sx={{ mb: 2 }}>{saveError}</Alert>}
                    <Grid container spacing={2}>
                        <Grid size={12}>
                            <TextField
                                id="extrapolation-item-name"
                                label="Name"
                                variant="outlined"
                                fullWidth
                                margin="normal"
                                value={name}
                                onChange={(e) =>
                                    setName(e.target.value as string)
                                }
                            ></TextField>
                        </Grid>
                        <Grid size={12}>
                            <TextField
                                id="extrapolation-item-amount"
                                label="Amount"
                                variant="outlined"
                                fullWidth
                                margin="normal"
                                value={amount}
                                onChange={(e) =>
                                    setAmount(parseFloat(e.target.value))
                                }
                            ></TextField>
                        </Grid>
                        <Grid size={12}>
                            <Select
                                id="extrapolation-item-type"
                                label="Type"
                                variant="outlined"
                                fullWidth
                                defaultValue="expense"
                                value={type}
                                onChange={(e) =>
                                    setType(e.target.value as string)
                                }
                            >
                                <MenuItem value="expense">Expense</MenuItem>
                                <MenuItem value="income">Income</MenuItem>
                            </Select>
                        </Grid>
                        <Grid size={12}>
                            <Select
                                id="extrapolation-item-income-date"
                                label="Income Date"
                                variant="outlined"
                                fullWidth
                                defaultValue="none"
                                value={incomeDate}
                                onChange={(e) =>
                                    setIncomeDate(e.target.value as string)
                                }
                            >
                                <MenuItem value="none">Income Date</MenuItem>
                                {sortedIncomeDates.map((date) => (
                                    <MenuItem key={date} value={date}>
                                        {date}
                                    </MenuItem>
                                ))}
                            </Select>
                        </Grid>
                        <Grid size={12}>
                            <FormGroup>
                                <FormControlLabel
                                    id="extrapolation-item-paid"
                                    control={
                                        <Switch
                                            checked={addingOneOffExpensePaid}
                                            onChange={() =>
                                                setAddingOneOffExpensePaid(
                                                    !addingOneOffExpensePaid,
                                                )
                                            }
                                        />
                                    }
                                    label="Paid"
                                />
                            </FormGroup>
                        </Grid>
                        <Grid size={12}>
                            {addingOneOffExpensePaid && (
                                <Select
                                    id="extrapolation-item-account"
                                    label="Account"
                                    variant="outlined"
                                    fullWidth
                                    value={account}
                                    onChange={(e) =>
                                        setAccount(e.target.value as string)
                                    }
                                >
                                    {profile.accounts.map((account) => (
                                        <MenuItem
                                            key={`account-${account.id}`}
                                            value={account.id}
                                        >
                                            {account.name}
                                        </MenuItem>
                                    ))}
                                </Select>
                            )}
                        </Grid>
                    </Grid>
                </Paper>
            </DialogContent>
            <DialogActions>
                <Button
                    onClick={close}
                    color="secondary"
                    variant="outlined"
                >
                    Cancel
                </Button>
                <Button
                    onClick={save}
                    variant="contained"
                >
                    Save
                </Button>
            </DialogActions>
        </Dialog>
    );
}
