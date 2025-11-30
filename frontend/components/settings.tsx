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

export default function Settings({ theme, swapTheme }) {
    const profile = useStore((state) => (state as any).profile);
    const budgetGroups = useStore((state) => (state as any).budgetGroups || []);
    
    // Settings state
    const [spreadsheetBackupLocation, setSpreadsheetBackupLocation] = React.useState<string>(
        localStorage.getItem('budgie:spreadsheetBackupLocation') || './schedule-spreadsheets/'
    );
    const [spreadsheetBackupCount, setSpreadsheetBackupCount] = React.useState<string>(
        localStorage.getItem('budgie:spreadsheetBackupCount') || '5000'
    );
    const [saveMessage, setSaveMessage] = React.useState<string>('');
    const [newBudgetGroupName, setNewBudgetGroupName] = React.useState<string>('');

    const saveSettings = () => {
        // Save settings to localStorage (or could be saved to backend/profile)
        localStorage.setItem('budgie:spreadsheetBackupLocation', spreadsheetBackupLocation);
        localStorage.setItem('budgie:spreadsheetBackupCount', spreadsheetBackupCount);
        
        setSaveMessage('Settings saved successfully!');
        setTimeout(() => setSaveMessage(''), 3000);
    };

    const removeBudgetGroup = async (budgetGroup) => {
        const confirm = window.confirm(`Are you sure you want to delete ${budgetGroup.name}?`);
        if (!confirm) {
            return;
        }
        await api.delete(`/budget/group/${profile.id}/${budgetGroup.id}`);
        fetchProfile(profile.id);
    };

    const addBudgetGroup = async () => {
        if (newBudgetGroupName.trim() === '') {
            return;
        }

        await api.post(`/budget/group/${profile.id}`, { name: newBudgetGroupName });
        setNewBudgetGroupName('');
        fetchProfile(profile.id);
    };

    return (
        <div>
            <Paper className="section" id="settings" elevation={2}>
                <h2>Settings</h2>
                <Grid container spacing={3}>
                    <Grid size={12}>
                        <Typography variant="h6" gutterBottom>
                            Appearance
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

                    <Grid size={12}>
                        <Typography variant="h6" gutterBottom style={{ marginTop: '20px' }}>
                            Spreadsheet Export Settings
                        </Typography>
                    </Grid>
                    
                    <Grid size={12}>
                        <TextField
                            fullWidth
                            label="Spreadsheet Backup Location"
                            value={spreadsheetBackupLocation}
                            onChange={(e) => setSpreadsheetBackupLocation(e.target.value)}
                            helperText="Directory path where exported spreadsheets will be saved"
                        />
                    </Grid>
                    
                    <Grid size={12}>
                        <TextField
                            fullWidth
                            type="number"
                            label="Spreadsheet Backup Count"
                            value={spreadsheetBackupCount}
                            onChange={(e) => setSpreadsheetBackupCount(e.target.value)}
                            helperText="Maximum number of backup spreadsheet files to keep"
                        />
                    </Grid>
                    
                    <Grid size={12}>
                        <Button
                            variant="contained"
                            color="primary"
                            onClick={saveSettings}
                        >
                            Save Settings
                        </Button>
                        {saveMessage && (
                            <Typography
                                variant="body2"
                                style={{ marginLeft: '16px', color: 'green', display: 'inline' }}
                            >
                                {saveMessage}
                            </Typography>
                        )}
                    </Grid>
                </Grid>
            </Paper>

            <Paper className="section" id="budget-groups" elevation={2} style={{ marginTop: '20px' }}>
                <h2>Budget Groups Management</h2>
                <Grid container spacing={3}>
                    <Grid size={12}>
                        <Typography variant="body1" gutterBottom>
                            Manage budget groups for organizing your budget items:
                        </Typography>
                        <div style={{ marginTop: '12px', marginBottom: '16px' }}>
                            {budgetGroups.map((budgetGroup) => (
                                <Chip 
                                    key={budgetGroup.id} 
                                    label={budgetGroup.name} 
                                    onDelete={() => removeBudgetGroup(budgetGroup)}
                                    style={{ margin: '4px' }}
                                />
                            ))}
                            {budgetGroups.length === 0 && (
                                <Typography variant="body2" color="textSecondary">
                                    No budget groups yet. Add one below.
                                </Typography>
                            )}
                        </div>
                    </Grid>
                    
                    <Grid size={12}>
                        <TextField
                            label="New Budget Group Name"
                            value={newBudgetGroupName}
                            onChange={(e) => setNewBudgetGroupName(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && addBudgetGroup()}
                            style={{ marginRight: '12px' }}
                        />
                        <Button 
                            variant="contained" 
                            color="primary"
                            onClick={addBudgetGroup}
                            disabled={!newBudgetGroupName.trim()}
                        >
                            Add Group
                        </Button>
                    </Grid>
                </Grid>
            </Paper>
            
            <Paper className="section" id="profile-info" elevation={2} style={{ marginTop: '20px' }}>
                <h2>Profile Information</h2>
                <Grid container spacing={2}>
                    <Grid size={12}>
                        <Typography>
                            <strong>Profile Name:</strong> {profile?.name}
                        </Typography>
                    </Grid>
                    <Grid size={12}>
                        <Typography>
                            <strong>Profile ID:</strong> {profile?.id}
                        </Typography>
                    </Grid>
                    {profile?.hidden_through && (
                        <Grid size={12}>
                            <Typography>
                                <strong>Hidden Through Date:</strong> {profile.hidden_through}
                            </Typography>
                            <Typography variant="caption" color="textSecondary">
                                Calendar columns before this date are hidden from view
                            </Typography>
                        </Grid>
                    )}
                </Grid>
            </Paper>
        </div>
    );
}
