import {
    Alert,
    Button,
    Grid,
    InputAdornment,
    InputLabel,
    MenuItem,
    OutlinedInput,
    Paper,
    Select,
    TextField,
    Typography,
} from '@mui/material';
import * as React from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import CurrencyLabel from './currency-label';
import Ledger from './ledger';
import { api } from './renderUtils';
import { fetchProfile, useStore } from '../store';

export default function Account({ accountId = '' }) {
    const params = useParams();
    const navigate = useNavigate();
    const profile = useStore((state) => (state as any).profile);

    if (params.accountId) {
        accountId = params.accountId;
    }

    const [account, setAccount] = React.useState<any>(
        profile.accounts.find(
            (account) => account.id === parseInt(accountId as string),
        ),
    );
    const [accountName, setAccountName] = React.useState<string>(
        account?.name || '',
    );
    const [accountType, setAccountType] = React.useState<string>(
        account?.type || 'checking',
    );
    const [accountBalance, setAccountBalance] = React.useState<number>(
        account?.balance || 0,
    );
    const [nameError, setNameError] = React.useState(false);
    const [balanceError, setBalanceError] = React.useState(false);
    const [error, setError] = React.useState('');

    function validate() {
        let fail = false;
        if (accountName === '') {
            setNameError(true);
            fail = true;
        } else {
            setNameError(false);
        }
        if (accountBalance === undefined || accountBalance === 0) {
            setBalanceError(true);
            fail = true;
        } else {
            setBalanceError(false);
        }

        return !fail;
    }

    async function save() {
        if (!validate()) {
            return;
        }

        try {
            const bodyData = {
                profileId: profile.id,
                name: accountName,
                type: accountType,
                balance: accountBalance,
            };
            let json;
            if (account?.id) {
                (bodyData as any).id = account.id;
                json = await api.put(`/accounts/${profile.id}/${account.id}`, bodyData);
            } else {
                json = await api.post(`/accounts/${profile.id}`, bodyData);
                setAccount(json);
            }
            // location.pathname = '#/accounts';
            fetchProfile(profile.id);
            navigate('/accounts');
            // notify profile
        } catch (err) {
            setError(err.message);
        }
    }

    return (
        <Paper className="section" id="account-details" elevation={2}>
            <Grid container spacing={2}>
                <Grid size={3} sx={{
                    padding: '48px',
                }}>
                    {error && (
                        <Grid size={12}>
                            <Alert severity="error">{error}</Alert>
                        </Grid>
                    )}
                    <Grid size={12}>
                        <InputLabel htmlFor="new-account-name">
                            Account Name
                        </InputLabel>
                        <TextField
                            autoFocus
                            id="new-account-name"
                            type="text"
                            required
                            error={nameError}
                            variant="outlined"
                            onChange={(e) => setAccountName(e.target.value)}
                            value={accountName}
                            inputProps={{ 'aria-label': 'account name' }}
                        />
                    </Grid>
                    <Grid size={12}>
                        <InputLabel htmlFor="new-account-type">
                            Account Type
                        </InputLabel>
                        <Select
                            id="new-account-type"
                            label="Account Type"
                            type="text"
                            required
                            variant="outlined"
                            value={accountType}
                            onChange={(e) => setAccountType(e.target.value)}
                            inputProps={{ 'aria-label': 'account type' }}
                            data-testid="account-type"
                        >
                            <MenuItem value="checking">Checking</MenuItem>
                            <MenuItem value="savings">Savings</MenuItem>
                            <MenuItem value="creditcard">Credit Card</MenuItem>
                            <MenuItem value="investment">Investment</MenuItem>
                        </Select>
                    </Grid>
                    <Grid size={12}>
                        <InputLabel htmlFor="new-account-balance">
                            Account Balance
                        </InputLabel>
                        <OutlinedInput
                            id="new-account-balance"
                            type="number"
                            required
                            error={balanceError}
                            inputProps={{ 'aria-label': 'account balance' }}
                            startAdornment={
                                <InputAdornment position="start">$</InputAdornment>
                            }
                            value={accountBalance}
                            onChange={(e) =>
                                setAccountBalance(
                                    (e.target as HTMLInputElement).valueAsNumber,
                                )
                            }
                        />
                    </Grid>
                    <Grid size={12}>
                        <Button variant="contained" color="primary" onClick={save}>
                            Save
                        </Button>
                    </Grid>
                </Grid>
                {accountId !== 'new' && (<Grid size={9}>
                    <Grid size={12}>
                        <Link to="/ledger/new">
                            <Button variant="outlined" color="secondary">
                                Add Ledger Item
                                <i className="material-icons">add</i>
                            </Button>
                        </Link>
                    </Grid>
                    <Grid size={12}>
                        {account?.ledger && account.ledger.length > 0 ? (
                            <Ledger
                                profile={profile}
                                account={account}
                                removeLedgerItem={() => {}}
                            />
                        ) : (
                            <Alert severity="info">
                                <Typography>
                                    No ledger items for this account.
                                </Typography>
                            </Alert>
                        )}
                    </Grid>
                </Grid>)}
            </Grid>
        </Paper>
    );
}
