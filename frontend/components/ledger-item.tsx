import {
    Alert,
    Divider,
    FormControlLabel,
    FormGroup,
    FormLabel,
    Grid,
    Paper,
    Switch,
} from '@mui/material';
import Button from '@mui/material/Button';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';
import TextField from '@mui/material/TextField';
import { LocalizationProvider } from '@mui/x-date-pickers';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { DesktopDatePicker } from '@mui/x-date-pickers/DesktopDatePicker';
import * as React from 'react';
import { useParams } from 'react-router-dom';
import DateLabel from './date-label';
import { api } from './renderUtils';
import { useStore } from '../store';

export default function LedgerItem({ ledgerItemId = '' }) {
    const params = useParams();
    const profile = useStore((state) => (state as any).profile);
    if (params.ledgerItemId) {
        ledgerItemId = params.ledgerItemId;
    }
    const ledgerItems = profile.accounts.reduce((acc, account) => {
        return [...acc, ...account.ledger];
    }, []);
    const [item, setItem] = React.useState<any>(
        ledgerItems.find(
            (ledgerItem) => ledgerItem.id === parseInt(ledgerItemId as string),
        ),
    );
    const budgetItems = profile.budget;

    const [ledgerName, setLedgerName] = React.useState(item?.name || '');
    const [ledgerAmount, setLedgerAmount] = React.useState(item?.amount || 0);
    const [ledgerType, setLedgerType] = React.useState(item?.type || 'expense');
    const [ledgerDate, setLedgerDate] = React.useState(
        item?.date || new Date(),
    );
    const [ledgerAccountId, setLedgerAccountId] = React.useState(
        item?.accountId || profile?.accounts[0]?.id,
    );
    const [ledgerBudgetItemId, setLedgerBudgetItemId] = React.useState(
        item?.budgetItemId || '',
    );
    const [ledgerExtrapolationItemId, setLedgerExtrapolationItemId] =
        React.useState(item?.extrapolationItemId || '');
    const [ledgerError, setLedgerError] = React.useState('');

    function changeBudgetItem(value) {
        console.log('new ledger budget item changed', value);
        const budgetItemId = parseInt(value, 10);
        const budgetItem = budgetItems.find(
            (budgetItem) => budgetItem.id === budgetItemId,
        );
        setLedgerName(budgetItem.name);
        setLedgerAmount(`-${budgetItem.amount.toString()}`);
        setLedgerBudgetItemId(budgetItemId);
        setLedgerExtrapolationItemId(budgetItem.extrapolationItems[0].id);
        setLedgerDate(budgetItem.extrapolationItems[0].date);
    }

    function changeExtrapolationItem(budgetExtrapolationItemId) {
        const intId = parseInt(budgetExtrapolationItemId, 10);
        setLedgerExtrapolationItemId(intId);
        for (const budgetItem of budgetItems) {
            for (const extrapolationItem of budgetItem.extrapolationItems) {
                if (extrapolationItem.id === intId) {
                    setLedgerDate(extrapolationItem.date);
                }
            }
        }
    }

    async function addOrUpdate() {
        const ledgerItem = {
            ...item,
            name: ledgerName,
            amount: parseFloat(ledgerAmount),
            type: ledgerType,
            date: ledgerDate,
            accountId: ledgerAccountId,
            budgetItemId: ledgerBudgetItemId,
            extrapolationItemId: ledgerExtrapolationItemId,
        };
        console.log('ledger item', ledgerItem);

        try {
            if (ledgerItem.id) {
                await api.put(
                    `/ledger/${profile.id}/${ledgerItem.id}`,
                    ledgerItem,
                );
            } else {
                await api.post(`/ledger/${profile.id}`, ledgerItem);
            }
        } catch (error) {
            setLedgerError(error.message);
        }
    }

    return (
        <Paper className="section" id="ledger-item" elevation={2}>
            <h2>Ledger Entry</h2>
            {ledgerError && <Alert severity="error">{ledgerError}</Alert>}
            <LocalizationProvider dateAdapter={AdapterDateFns}>
                <form>
                    <Grid
                        container
                        spacing={2}
                        sx={{ marginTop: '4px', marginBottom: '4px' }}
                    >
                        <Grid className="form-field" size={12}>
                            <FormLabel
                                sx={{ width: '200px' }}
                                htmlFor="new-legder-item-name"
                            >
                                Ledger Entry Name
                            </FormLabel>
                            <TextField
                                id="new-ledger-item-name"
                                label="Name"
                                type="text"
                                variant="standard"
                                defaultValue={ledgerName ?? ''}
                                fullWidth
                            />
                        </Grid>
                        <Grid className="form-field" size={12}>
                            <FormLabel
                                sx={{ width: '200px' }}
                                htmlFor="new-legder-item-amount"
                            >
                                Ledger Entry Amount
                            </FormLabel>
                            <TextField
                                id="new-ledger-item-amount"
                                label="Amount"
                                type="number"
                                variant="standard"
                                defaultValue={ledgerAmount}
                                fullWidth
                            />
                        </Grid>
                        <Grid className="form-field" size={12}>
                            <FormLabel
                                sx={{ width: '200px' }}
                                htmlFor="new-legder-item-account"
                            >
                                Ledger Entry Account
                            </FormLabel>
                            <Select
                                id="new-ledger-item-account"
                                label="Account"
                                type="text"
                                variant="standard"
                                value={ledgerAccountId}
                                onChange={(e) =>
                                    setLedgerAccountId(
                                        parseInt(e.target.value, 10),
                                    )
                                }
                                inputProps={{
                                    'data-testid': 'new-ledger-item-account',
                                }}
                                fullWidth
                            >
                                {profile.accounts.map((account) => {
                                    return (
                                        <MenuItem
                                            key={account.id}
                                            value={account.id}
                                            selected={
                                                account.id === ledgerAccountId
                                            }
                                        >
                                            {account.name}
                                        </MenuItem>
                                    );
                                })}
                            </Select>
                        </Grid>
                        <Grid size={12}>
                            <FormGroup>
                                <Grid container>
                                    <FormLabel
                                        sx={{ display: 'inline-block' }}
                                        component="legend"
                                    >
                                        Income
                                    </FormLabel>
                                    <Switch
                                        id="new-ledger-item-type"
                                        defaultChecked
                                        onChange={(e) => {
                                            setLedgerType(
                                                e.target.checked
                                                    ? 'income'
                                                    : 'expense',
                                            );
                                        }}
                                        inputProps={{
                                            'aria-label': 'Account Type',
                                        }}
                                    />
                                    <FormLabel
                                        sx={{ display: 'inline-block' }}
                                        component="legend"
                                    >
                                        Expense
                                    </FormLabel>
                                </Grid>
                            </FormGroup>
                        </Grid>
                        <Grid size={12}>
                            <DesktopDatePicker
                                label="Date"
                                // inputFormat="MM/dd/yyyy"
                                value={ledgerDate ?? new Date()}
                                onChange={(value) =>
                                    setLedgerDate(value as Date)
                                }
                                // renderInput={(params) => (
                                //     <TextField {...params} />
                                // )}
                            />
                        </Grid>
                        <Grid size={12}>
                            <Divider />
                        </Grid>
                        <Grid size={12}>
                            <h3>
                                Associate this ledger entry with a budget item
                                entry.
                            </h3>
                        </Grid>
                        <Grid className="form-field" size={6}>
                            <Select
                                id="new-ledger-item-budget-item"
                                label="Associated Budget Item"
                                type="text"
                                variant="standard"
                                value={ledgerBudgetItemId}
                                fullWidth
                                inputProps={{
                                    'data-testid':
                                        'new-ledger-item-budget-item',
                                }}
                                onChange={(e) =>
                                    changeBudgetItem(e.target.value)
                                }
                            >
                                <MenuItem key="none" value="">
                                    No Budget Item
                                </MenuItem>
                                {budgetItems.map((budgetItem) => {
                                    return (
                                        <MenuItem
                                            key={budgetItem.id}
                                            value={budgetItem.id}
                                        >
                                            {budgetItem.name}
                                        </MenuItem>
                                    );
                                })}
                            </Select>
                        </Grid>
                        <Grid className="form-field" size={6}>
                            <Select
                                id="new-ledger-item-extrapolation-item"
                                label="Associated Extrapolation Item"
                                type="text"
                                variant="standard"
                                fullWidth
                                value={ledgerExtrapolationItemId || ''}
                                inputProps={{
                                    'data-testid':
                                        'new-ledger-item-extrapolation-item',
                                }}
                                onChange={(e) =>
                                    changeExtrapolationItem(e.target.value)
                                }
                            >
                                <MenuItem key="none" value="">
                                    No Budget Item Date
                                </MenuItem>
                                {ledgerBudgetItemId
                                    ? budgetItems
                                          .find(
                                              (b) =>
                                                  b.id === ledgerBudgetItemId,
                                          )
                                          .extrapolationItems.map(
                                              (extrapolationItem) => {
                                                  return (
                                                      <MenuItem
                                                          key={
                                                              extrapolationItem.id
                                                          }
                                                          value={
                                                              extrapolationItem.id
                                                          }
                                                      >
                                                          {<DateLabel date={extrapolationItem.date} />}
                                                      </MenuItem>
                                                  );
                                              },
                                          )
                                    : null}
                            </Select>
                        </Grid>
                        <Grid size={12} sx={{ marginTop: '8px' }}>
                            <Button
                                data-testid="new-ledger-item-submit"
                                variant="contained"
                                onClick={() => addOrUpdate()}
                            >
                                Save
                                <i className="material-icons">save</i>
                            </Button>
                        </Grid>
                    </Grid>
                </form>
            </LocalizationProvider>
        </Paper>
    );
}
