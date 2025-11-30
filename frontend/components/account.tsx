import {
    Alert,
    Box,
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
import { useTheme } from '@mui/material/styles';
import { Link, useParams, useNavigate } from 'react-router-dom';
import CurrencyLabel from './currency-label';
import Ledger from './ledger';
import { api } from './renderUtils';
import { fetchProfile, useStore } from '../store';

export default function Account({ accountId = '' }) {
    const theme = useTheme();
    const { accountId: id } = useParams<{ accountId: string }>();
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
        (account?.type || 'checking').toLowerCase(),
    );
    const [accountBalance, setAccountBalance] = React.useState<number>(
        account?.balance || 0,
    );
    const [nameError, setNameError] = React.useState(false);
    const [balanceError, setBalanceError] = React.useState(false);
    const [error, setError] = React.useState('');

    // Update account when profile changes (e.g., after fetching ledger entries)
    React.useEffect(() => {
        const updatedAccount = profile.accounts.find(
            (acc) => acc.id === parseInt(accountId as string),
        );
        if (updatedAccount) {
            console.log('Updated account:', updatedAccount);
            console.log('Account type from API:', updatedAccount.type);
            console.log('Account ledger:', updatedAccount.ledger);
            setAccount(updatedAccount);
            setAccountName(updatedAccount.name || '');
            // Normalize account type to lowercase to match dropdown values
            const normalizedType = (updatedAccount.type || 'checking').toLowerCase();
            console.log('Normalized account type:', normalizedType);
            setAccountType(normalizedType);
            setAccountBalance(updatedAccount.balance || 0);
        }
    }, [profile, accountId]);

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

    const accountIcons = {
        'checking': '💳',
        'savings': '🏦',
        'creditcard': '💎',
        'credit card': '💎',
        'investment': '💰',
    };
    
    const icon = accountIcons[accountType?.toLowerCase()] || '💰';

    return (
        <Paper className="section" id="account-details" elevation={2} sx={{ p: 0 }}>
            {/* Header Section */}
            <Box sx={{
                backgroundColor: theme.palette.mode === 'dark' ? '#263238' : '#e0e0e0',
                borderRadius: '8px 8px 0 0',
                padding: '20px',
            }}>
                {/* Back button */}
                <Link to="/accounts" style={{ textDecoration: 'none' }}>
                    <Button
                        variant="outlined"
                        sx={{
                            mb: 2,
                            color: theme.palette.mode === 'dark' ? '#fff' : '#000',
                            borderColor: theme.palette.mode === 'dark' ? '#546e7a' : '#90a4ae',
                            '&:hover': {
                                borderColor: theme.palette.mode === 'dark' ? '#78909c' : '#607d8b',
                                backgroundColor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.04)',
                            }
                        }}
                    >
                        ⬅️ Back to Accounts
                    </Button>
                </Link>

                {/* Account title with icon */}
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 3 }}>
                    <Typography sx={{ fontSize: '2.5rem' }}>
                        {icon}
                    </Typography>
                    <Typography variant="h4" sx={{ 
                        fontWeight: 'bold', 
                        color: theme.palette.mode === 'dark' ? '#fff' : '#000'
                    }}>
                        {accountId === 'new' ? 'New Account' : accountName}
                    </Typography>
                </Box>

                {error && (
                    <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>
                )}

                {/* Account form controls in horizontal layout */}
                <Box sx={{ 
                    display: 'flex', 
                    gap: 2, 
                    alignItems: 'flex-end',
                    flexWrap: 'wrap'
                }}>
                    <Box sx={{ flex: 1, minWidth: 200 }}>
                        <InputLabel htmlFor="new-account-name" sx={{ 
                            color: theme.palette.mode === 'dark' ? '#90a4ae' : '#546e7a', 
                            mb: 1,
                            fontSize: 12,
                            fontWeight: 'bold'
                        }}>
                            Account Name
                        </InputLabel>
                        <TextField
                            autoFocus
                            id="new-account-name"
                            type="text"
                            required
                            fullWidth
                            size="small"
                            error={nameError}
                            variant="outlined"
                            onChange={(e) => setAccountName(e.target.value)}
                            value={accountName}
                            inputProps={{ 'aria-label': 'account name' }}
                        />
                    </Box>
                    <Box sx={{ minWidth: 180 }}>
                        <InputLabel htmlFor="new-account-type" sx={{ 
                            color: theme.palette.mode === 'dark' ? '#90a4ae' : '#546e7a', 
                            mb: 1,
                            fontSize: 12,
                            fontWeight: 'bold'
                        }}>
                            Account Type
                        </InputLabel>
                        <Select
                            id="new-account-type"
                            type="text"
                            required
                            fullWidth
                            size="small"
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
                    </Box>
                    <Box sx={{ minWidth: 180 }}>
                        <InputLabel htmlFor="new-account-balance" sx={{ 
                            color: theme.palette.mode === 'dark' ? '#90a4ae' : '#546e7a', 
                            mb: 1,
                            fontSize: 12,
                            fontWeight: 'bold'
                        }}>
                            Account Balance
                        </InputLabel>
                        <OutlinedInput
                            id="new-account-balance"
                            type="number"
                            required
                            fullWidth
                            size="small"
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
                    </Box>
                    <Button 
                        variant="contained" 
                        color="primary" 
                        onClick={save}
                        sx={{ 
                            fontWeight: 'bold',
                            px: 3,
                            py: 1
                        }}
                    >
                        💾 Save Account
                    </Button>
                </Box>
            </Box>

            {/* Account info stats section */}
            {accountId !== 'new' && (
                <Box sx={{ p: 3, pb: 0 }}>
                    <Box sx={{
                        backgroundColor: theme.palette.mode === 'dark' ? '#37474f' : '#f5f5f5',
                        borderRadius: '8px',
                        padding: '20px',
                        display: 'flex',
                        gap: 4,
                        alignItems: 'center'
                    }}>
                        <Box>
                            <Typography sx={{ fontSize: 12, color: '#90a4ae', fontWeight: 'bold', mb: 1 }}>
                                Account Type
                            </Typography>
                            <Typography variant="h6">
                                {accountType || 'N/A'}
                            </Typography>
                        </Box>
                        <Box>
                            <Typography sx={{ fontSize: 12, color: '#90a4ae', fontWeight: 'bold', mb: 1 }}>
                                Current Balance
                            </Typography>
                            <Typography variant="h5" sx={{ fontWeight: 'bold', color: '#4caf50' }}>
                                <CurrencyLabel amount={account?.balance || 0} />
                            </Typography>
                        </Box>
                        <Box>
                            <Typography sx={{ fontSize: 12, color: '#90a4ae', fontWeight: 'bold', mb: 1 }}>
                                Ledger Entries
                            </Typography>
                            <Typography variant="h6">
                                {account?.ledger?.length || 0}
                            </Typography>
                        </Box>
                        <Box sx={{ flex: 1 }} />
                        <Link to="/ledger/new" style={{ textDecoration: 'none' }}>
                            <Button 
                                variant="contained" 
                                color="primary"
                                sx={{ fontWeight: 'bold' }}
                            >
                                ➕ Add Ledger Entry
                            </Button>
                        </Link>
                    </Box>
                </Box>
            )}

            {/* Ledger table - full width */}
            {accountId !== 'new' && (
                <Box sx={{ p: 3 }}>
                    <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold' }}>
                        📊 Ledger Entries ({account?.ledger?.length || 0})
                    </Typography>
                    {account?.ledger && account.ledger.length > 0 ? (
                        <Ledger
                            profile={profile}
                            account={account}
                            removeLedgerItem={() => {}}
                        />
                    ) : (
                        <Box sx={{
                            backgroundColor: theme.palette.mode === 'dark' ? '#37474f' : '#f5f5f5',
                            borderRadius: '8px',
                            padding: '40px',
                            textAlign: 'center'
                        }}>
                            <Typography sx={{ color: '#90a4ae' }}>
                                No ledger entries yet. Add one to get started!
                            </Typography>
                        </Box>
                    )}
                </Box>
            )}
        </Paper>
    );
}
