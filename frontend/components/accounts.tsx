import {
    Box,
    Card,
    CardContent,
    Typography,
} from '@mui/material';
import Button from '@mui/material/Button';
import Paper from '@mui/material/Paper';
import * as React from 'react';
import { useTheme } from '@mui/material/styles';
import { Link } from 'react-router-dom';
import CurrencyLabel from './currency-label';
import HelpIcon from './help-icon';
import { useStore } from '../store';

const accountIcons = {
    'checking': '💳',
    'savings': '🏦',
    'credit card': '💎',
};

const accountBgColorsDark = {
    'checking': '#37474f',
    'savings': '#1e3a5f',
    'credit card': '#4a2c2a',
};

const accountBgColorsLight = {
    'checking': '#b2dfdb',
    'savings': '#b3e5fc',
    'credit card': '#ffcdd2',
};

export default function Accounts() {
    const accounts = useStore((state) => (state as any).accounts);
    const profile = useStore((state) => (state as any).profile);
    const theme = useTheme();

    return (
        <Paper className="section" id="accounts" elevation={2} sx={{ p: 0 }}>
            {/* Title Section */}
            <Box sx={{
                backgroundColor: theme.palette.mode === 'dark' ? '#263238' : '#e0e0e0',
                borderRadius: '8px 8px 0 0',
                padding: '15px 20px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
            }}>
                <Typography variant="h4" sx={{ fontWeight: 'bold', m: 0 }}>
                    💼 Accounts
                    <HelpIcon text="Add your bank accounts here. Each account tracks its own ledger of transactions." />
                </Typography>
                <Link to="/accounts/new" style={{ textDecoration: 'none' }}>
                    <Button
                        className="add-account-button"
                        variant="contained"
                        color="primary"
                        sx={{
                            fontWeight: 'bold',
                            px: 3
                        }}
                    >
                        ➕ Add Account
                    </Button>
                </Link>
            </Box>

            {/* Accounts Grid */}
            <Box sx={{ p: 3 }}>
                {accounts.length > 0 ? (
                    <Box sx={{
                        display: 'flex',
                        gap: 3,
                        flexWrap: 'wrap',
                        justifyContent: 'center'
                    }}>
                        {accounts.map((account) => {
                            const accountType = account.type?.toLowerCase() || 'checking';
                            const icon = accountIcons[accountType] || '💰';
                            const isDarkMode = theme.palette.mode === 'dark';
                            const bgColor = isDarkMode 
                                ? (accountBgColorsDark[accountType] || '#37474f')
                                : (accountBgColorsLight[accountType] || '#b2dfdb');
                            const borderColor = isDarkMode ? '#546e7a' : '#90a4ae';
                            const textColor = isDarkMode ? 'white' : '#1a1a1a';
                            
                            return (
                                <Card
                                    key={account.id}
                                    sx={{
                                        minWidth: 280,
                                        maxWidth: 300,
                                        minHeight: 200,
                                        backgroundColor: bgColor,
                                        border: `2px solid ${borderColor}`,
                                        borderRadius: '10px',
                                        transition: 'all 0.3s ease',
                                        '&:hover': {
                                            borderColor: '#1976d2',
                                            transform: 'translateY(-4px)',
                                            boxShadow: 4
                                        }
                                    }}
                                >
                                    <CardContent sx={{ p: 2.5 }}>
                                        {/* Account name with icon */}
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                                            <Typography sx={{ fontSize: '2rem' }}>
                                                {icon}
                                            </Typography>
                                            <Typography variant="h6" sx={{ fontWeight: 'bold', color: textColor }}>
                                                {account.name}
                                            </Typography>
                                        </Box>

                                        <Box sx={{ borderTop: `1px solid ${borderColor}`, pt: 2, mb: 2 }} />

                                        {/* Account type */}
                                        <Typography sx={{ fontSize: 12, color: isDarkMode ? '#90a4ae' : '#546e7a', mb: 1 }}>
                                            Type: {account.type || 'N/A'}
                                        </Typography>

                                        {/* Current Balance label */}
                                        <Typography sx={{ fontSize: 11, color: isDarkMode ? '#b0bec5' : '#607d8b', mb: 0.5, fontWeight: 'bold' }}>
                                            Current Balance
                                        </Typography>

                                        {/* Balance */}
                                        <Typography variant="h5" sx={{ 
                                            fontWeight: 'bold', 
                                            color: '#4caf50',
                                            my: 1
                                        }}>
                                            <CurrencyLabel amount={account.balance} />
                                        </Typography>

                                        {/* Ledger entry count */}
                                        <Typography sx={{ fontSize: 11, color: isDarkMode ? '#b0bec5' : '#78909c', mb: 2 }}>
                                            {account?.ledger?.length > 0
                                                ? `${account.ledger.length} ledger entries`
                                                : 'No ledger entries'}
                                        </Typography>

                                        {/* View button */}
                                        <Link to={`/accounts/${account.id}`} style={{ textDecoration: 'none' }}>
                                            <Button
                                                variant="contained"
                                                fullWidth
                                                sx={{
                                                    fontWeight: 'bold',
                                                    fontSize: 12
                                                }}
                                            >
                                                View Details
                                            </Button>
                                        </Link>
                                    </CardContent>
                                </Card>
                            );
                        })}
                    </Box>
                ) : (
                    <Typography 
                        sx={{ 
                            textAlign: 'center', 
                            color: '#90a4ae', 
                            fontSize: 14, 
                            py: 5 
                        }}
                    >
                        Accounts represent your bank accounts — checking, savings, credit cards. Each account has a ledger that tracks transactions. Click 'Add Account' above to create your first one.
                    </Typography>
                )}
            </Box>
        </Paper>
    );
}
