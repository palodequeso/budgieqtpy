import { Alert, Box, ButtonGroup, Typography } from '@mui/material';
import Button from '@mui/material/Button';
import Paper from '@mui/material/Paper';
import * as React from 'react';
import { useTheme } from '@mui/material/styles';
import { Link } from 'react-router-dom';
import { api } from './renderUtils';
import BudgetTable from './budget-table';
import BudgetCards from './budget-cards';
import BudgetChart from './budget-chart';
import { fetchProfile, useStore } from '../store';

export default function Budget() {
    const theme = useTheme();
    const [budgetTableError, setBudgetTableError] = React.useState(null);
    const [view, setView] = React.useState('list');
    const profile = useStore((state) => (state as any).profile);

    const removeBudgetItem = async (budgetItemId) => {
        try {
            await api.delete(`/budget/${profile.id}/${budgetItemId}`);
            fetchProfile(profile.id);
        } catch (err) {
            setBudgetTableError(err.message);
        }
    };

    return (
        <Paper className="section" id="budget" elevation={2} sx={{ p: 0 }}>
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
                    💰 Budget Items
                </Typography>
                <Link to="/budget/new" style={{ textDecoration: 'none' }}>
                    <Button
                        className="add-budget-item-button"
                        variant="contained"
                        color="primary"
                        sx={{
                            fontWeight: 'bold',
                            px: 3
                        }}
                    >
                        ➕ Add Budget Item
                    </Button>
                </Link>
            </Box>

            {/* Content */}
            <Box sx={{ p: 3 }}>
                {budgetTableError && (
                    <Alert severity="error" sx={{ mb: 2 }}>{budgetTableError}</Alert>
                )}

                {view === 'list' && (<BudgetTable removeBudgetItem={removeBudgetItem} />)}
                {view === 'cards' && (<BudgetCards removeBudgetItem={removeBudgetItem} />)}
                {view === 'chart' && (<BudgetChart />)}
            </Box>
        </Paper>
    );
}
