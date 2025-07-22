import { Alert, ButtonGroup, Tab } from '@mui/material';
import Button from '@mui/material/Button';
import Paper from '@mui/material/Paper';
import * as React from 'react';
import { Link } from 'react-router-dom';
import { api } from './renderUtils';
import BudgetTable from './budget-table';
import BudgetCards from './budget-cards';
import BudgetChart from './budget-chart';
import { fetchProfile, useStore } from '../store';

export default function Budget() {
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
        <Paper className="section" id="budget" elevation={2}>
            <h2>Budgie</h2>
            {budgetTableError && (
                <Alert severity="error">{budgetTableError}</Alert>
            )}
            <ButtonGroup variant="contained" aria-label="outlined primary button group">
                <Button disabled={view === 'list'} onClick={() => setView('list')}>List</Button>
                <Button disabled={view === 'cards'} onClick={() => setView('cards')}>Cards</Button>
                <Button disabled={view === 'chart'} onClick={() => setView('chart')}>Chart</Button>
            </ButtonGroup>
            <Link to="/budget/new">
                <Button
                    className="add-budget-item-button"
                    variant="contained"
                    color="primary"
                >
                    Add Budget Item
                    <i className="material-icons">add</i>
                </Button>
            </Link>
            {view === 'list' && (<BudgetTable removeBudgetItem={removeBudgetItem} />)}
            {view === 'cards' && (<BudgetCards removeBudgetItem={removeBudgetItem} />)}
            {view === 'chart' && (<BudgetChart />)}
        </Paper>
    );
}
