import {
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
    Card,
} from '@mui/material';
import * as React from 'react';
import CurrencyLabel from './currency-label';
import { api } from './renderUtils';
import { fetchProfile } from '../store';

export default function CalendarSavingsItems({ open, profile, close }) {
    const [computed, setComputed] = React.useState(false);
    const [savingsAccount, setSavingsAccount] = React.useState('');
    const [spendingBuffer, setSpendingBuffer] = React.useState(400);
    const [computedSavingsItems, setComputedSavingsItems] = React.useState([]); // matches order of sortedIncomeDates

    React.useEffect(() => {
        const savingsAccounts = profile.accounts.filter(account => account.type === 'savings');
        if (savingsAccounts.length > 0) {
            setSavingsAccount(savingsAccounts[0].id);
        }
    }, [profile.accounts]);

    async function save() {
        await api.post(`/calendar/${profile.id}/savecomputedsavings`, {
            addedEntries: computedSavingsItems,
            savingsAccount,
        });
        close(true); // Pass true to indicate successful save
        fetchProfile(profile.id);
    }

    async function computeSavingsItems() {
        const result = await api.post(`/calendar/${profile.id}/computesavings`, {
            savingsAccount,
            spendingBuffer,
        });
        console.log('result', result);
        setComputedSavingsItems(result.addedEntries);
        setComputed(true);
    }

    return (
        <Dialog open={open} onClose={() => close(false)} maxWidth="md" fullWidth>
            <DialogTitle>Add Savings Items</DialogTitle>
            <DialogContent>
                <Paper>
                    <h4>Add Extrapolation/Budget Item</h4>
                    <Grid container spacing={2}>
                        {/* <Grid size={12}>
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
                        </Grid> */}
                        <Grid size={12}>
                            <TextField
                                id="extrapolation-item-amount"
                                label="Amount"
                                variant="outlined"
                                fullWidth
                                margin="normal"
                                value={spendingBuffer}
                                onChange={(e) =>
                                    setSpendingBuffer(parseFloat(e.target.value))
                                }
                            ></TextField>
                        </Grid>
                        <Grid size={12}>
                            <Select
                                id="extrapolation-item-account"
                                label="Account"
                                variant="outlined"
                                fullWidth
                                value={savingsAccount}
                                onChange={(e) =>
                                    setSavingsAccount(e.target.value as string)
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
                        </Grid>
                    </Grid>
                </Paper>
                {computed && computedSavingsItems.length > 0 && (
                    <Paper>
                        <h4>Computed Savings Items</h4>
                        {computedSavingsItems.map((item, i) => {
                            return (<Card elevation={4} key={(item as any).date} sx={{
                                display: 'inline-block',
                                marginRight: '8px',
                            }}>
                                <div style={{
                                    fontWeight: 'bold',
                                }}>{(item as any).date}</div>
                                <CurrencyLabel amount={(item as any).amount} />
                            </Card>);
                        })}
                    </Paper>
                )}
                {computed && computedSavingsItems.length === 0 && (
                    <Paper>
                        <h4>No room for savings with this threshold. :(</h4>
                    </Paper>
                )}
            </DialogContent>
            <DialogActions>
                <Button
                    onClick={computeSavingsItems}
                    variant="contained"
                >
                    Compute Savings Items
                </Button>
                <Button
                    onClick={() => close(false)}
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
