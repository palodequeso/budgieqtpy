import {
    Button,
    Chip,
    FormControlLabel,
    FormGroup,
    Grid,
    Paper,
    Switch,
    TextField,
    Typography,
} from '@mui/material';
import * as React from 'react';
import { fetchProfile, useStore } from '../store';
import { api } from './renderUtils';

export default function Profile({ theme, swapTheme }) {
    const [newBudgetItemGroupName, setNewBudgetItemGroupName] = React.useState<string>('');
    const profile = useStore((state) => (state as any).profile);
    const budgetGroups = useStore((state) => (state as any).budgetGroups || []);

    const removeBudgetGroup = async (budgetGroup) => {
        const confirm = window.confirm(`Are you sure you want to delete ${budgetGroup.name}?`);
        if (!confirm) {
            return;
        }
        await api.delete(`/budget/group/${profile.id}/${budgetGroup.id}`);
        fetchProfile(profile.id);
    };

    const addBudgetGroup = async () => {
        if (newBudgetItemGroupName === '') {
            return;
        }

        await api.post(`/budget/group/${profile.id}`, { name: newBudgetItemGroupName });

        // setPreviousBudgetItemGroupNames([...previousBudgetItemGroupNames, newBudgetItemGroupName]);
        setNewBudgetItemGroupName('');
        fetchProfile(profile.id);
    }

    return (<div>
        <Paper className="section" id="profile" elevation={2}>
            <h2>Profile</h2>
            <Grid container spacing={2}>
                <Grid size={12}>
                    <Typography>
                        <strong>Name:</strong> {profile.name}
                    </Typography>
                </Grid>
                <Grid size={12}>
                    <FormGroup>
                        <FormControlLabel
                            control={
                                <Switch
                                    checked={theme === 'dark'}
                                    onChange={swapTheme}
                                />
                            }
                            label="Dark Mode"
                        />
                    </FormGroup>
                </Grid>
            </Grid>
        </Paper>
        <Paper className="section" id="profile" elevation={2}>
            <h2>Budget Groups</h2>
            <div>
                {budgetGroups.map((budgetGroup) => (
                    <Chip key={budgetGroup.id} label={budgetGroup.name} onDelete={() => removeBudgetGroup(budgetGroup)} />
                ))}
            </div>
            <div>
                <FormControlLabel
                    control={
                        <TextField
                            label="New Group Name"
                            id="new-group-name"
                            value={newBudgetItemGroupName}
                            onChange={(e) => setNewBudgetItemGroupName(e.target.value)}
                            sx={{ marginLeft: '8px' }}
                        />
                    }
                    label="Budget Item New Group Name"
                    labelPlacement="start"
                    sx={{ marginRight: '4px' }}
                />
                <Button onClick={() => addBudgetGroup()} >Add Group Name</Button>
            </div>
        </Paper>
    </div>);
}
