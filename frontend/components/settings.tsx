import {
    Alert,
    Box,
    Button,
    Chip,
    FormControlLabel,
    FormGroup,
    Grid,
    Paper,
    Snackbar,
    Switch,
    TextField,
    Typography,
} from '@mui/material';
import * as React from 'react';
import { fetchProfile, fetchProfiles, useStore } from '../store';
import { api } from './renderUtils';
import OnboardingDialog from './onboarding';

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
    const [aiServerUrl, setAiServerUrl] = React.useState('');
    const [aiModel, setAiModel] = React.useState('qwen2.5:0.5b');
    const [aiEnabled, setAiEnabled] = React.useState(false);
    const [aiSaveMessage, setAiSaveMessage] = React.useState('');
    const [showOnboarding, setShowOnboarding] = React.useState(false);

    // Export/Import state
    const [exportImportSnackbar, setExportImportSnackbar] = React.useState('');
    const [importError, setImportError] = React.useState('');
    const [exporting, setExporting] = React.useState(false);
    const [importing, setImporting] = React.useState(false);
    const fileInputRef = React.useRef<HTMLInputElement>(null);

    const handleExportProfile = async () => {
        if (!profile?.id) return;
        setExporting(true);
        setImportError('');
        try {
            const data = await api.get(`/profile/${profile.id}/export`);
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${profile.name || 'profile'}-export.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            setExportImportSnackbar('Profile exported successfully!');
        } catch (err: any) {
            setImportError(err.message || 'Failed to export profile');
        } finally {
            setExporting(false);
        }
    };

    const handleImportProfile = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;
        setImporting(true);
        setImportError('');
        try {
            const text = await file.text();
            const jsonData = JSON.parse(text);
            const result = await api.post('/profile/import', jsonData) as any;
            const newName = result?.name || result?.profile?.name || 'Imported profile';
            setExportImportSnackbar(`Profile "${newName}" imported successfully!`);
            fetchProfiles();
        } catch (err: any) {
            if (err instanceof SyntaxError) {
                setImportError('Invalid JSON file. Please select a valid profile export file.');
            } else {
                setImportError(err.message || 'Failed to import profile');
            }
        } finally {
            setImporting(false);
            // Reset the file input so the same file can be selected again
            if (fileInputRef.current) {
                fileInputRef.current.value = '';
            }
        }
    };

    const saveSettings = () => {
        // Save settings to localStorage (or could be saved to backend/profile)
        localStorage.setItem('budgie:spreadsheetBackupLocation', spreadsheetBackupLocation);
        localStorage.setItem('budgie:spreadsheetBackupCount', spreadsheetBackupCount);
        
        setSaveMessage('Settings saved successfully!');
        setTimeout(() => setSaveMessage(''), 3000);
    };

    const [groupError, setGroupError] = React.useState('');
    const [groupSuccess, setGroupSuccess] = React.useState('');

    const removeBudgetGroup = async (budgetGroup) => {
        const confirm = window.confirm(`Are you sure you want to delete ${budgetGroup.name}?`);
        if (!confirm) {
            return;
        }
        try {
            await api.delete(`/budget/group/${profile.id}/${budgetGroup.id}`);
            setGroupSuccess(`Budget group '${budgetGroup.name}' deleted.`);
            setTimeout(() => setGroupSuccess(''), 3000);
            fetchProfile(profile.id);
        } catch (err) {
            setGroupError(err.message);
            setTimeout(() => setGroupError(''), 5000);
        }
    };

    React.useEffect(() => {
        api.get('/ai/config').then((config: any) => {
            setAiServerUrl(config.server_url || '');
            setAiModel(config.model || 'qwen2.5:0.5b');
            setAiEnabled(config.enabled || false);
        }).catch(() => {});
    }, []);

    const saveAiSettings = async () => {
        try {
            await api.put('/ai/config', {
                server_url: aiServerUrl,
                model: aiModel,
                enabled: aiEnabled,
            });
            setAiSaveMessage('AI settings saved!');
            setTimeout(() => setAiSaveMessage(''), 3000);
        } catch (e) {
            setAiSaveMessage('Failed to save AI settings');
        }
    };

    const addBudgetGroup = async () => {
        if (newBudgetGroupName.trim() === '') {
            return;
        }

        try {
            await api.post(`/budget/group/${profile.id}`, { name: newBudgetGroupName });
            setNewBudgetGroupName('');
            setGroupSuccess(`Budget group '${newBudgetGroupName}' created.`);
            setTimeout(() => setGroupSuccess(''), 3000);
            fetchProfile(profile.id);
        } catch (err) {
            setGroupError(err.message);
            setTimeout(() => setGroupError(''), 5000);
        }
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
                        {groupError && <Alert severity="error" sx={{ mb: 1 }}>{groupError}</Alert>}
                        {groupSuccess && <Alert severity="success" sx={{ mb: 1 }}>{groupSuccess}</Alert>}
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

            <Paper className="section" id="ai-settings" elevation={2} style={{ marginTop: '20px' }}>
                <h2>AI Budget Analysis</h2>
                <Grid container spacing={3}>
                    <Grid size={12}>
                        <FormGroup>
                            <FormControlLabel
                                control={
                                    <Switch
                                        checked={aiEnabled}
                                        onChange={(e) => setAiEnabled(e.target.checked)}
                                    />
                                }
                                label="Enable AI Analysis"
                            />
                        </FormGroup>
                    </Grid>

                    <Grid size={12}>
                        <TextField
                            fullWidth
                            label="Server URL"
                            value={aiServerUrl}
                            onChange={(e) => setAiServerUrl(e.target.value)}
                            helperText="OpenAI-compatible endpoint, e.g. http://localhost:11434/v1 for Ollama"
                        />
                    </Grid>

                    <Grid size={12}>
                        <TextField
                            fullWidth
                            label="Model"
                            value={aiModel}
                            onChange={(e) => setAiModel(e.target.value)}
                            helperText="Model to use, e.g. qwen2.5:0.5b"
                        />
                    </Grid>

                    <Grid size={12}>
                        <Button
                            variant="contained"
                            color="primary"
                            onClick={saveAiSettings}
                        >
                            Save AI Settings
                        </Button>
                        {aiSaveMessage && (
                            <Typography
                                variant="body2"
                                style={{ marginLeft: '16px', color: 'green', display: 'inline' }}
                            >
                                {aiSaveMessage}
                            </Typography>
                        )}
                    </Grid>

                    <Grid size={12}>
                        <Typography variant="body2" color="textSecondary">
                            Install Ollama and run: ollama pull qwen2.5:0.5b
                        </Typography>
                    </Grid>
                </Grid>
            </Paper>
            <Paper className="section" id="export-import" elevation={2} style={{ marginTop: '20px' }}>
                <h2>Export &amp; Import</h2>
                <Grid container spacing={3}>
                    <Grid size={12}>
                        <Typography variant="body1" gutterBottom>
                            Export your current profile to a JSON file, or import a previously exported profile.
                        </Typography>
                        {importError && <Alert severity="error" sx={{ mb: 2 }}>{importError}</Alert>}
                    </Grid>

                    <Grid size={12}>
                        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                            <Button
                                variant="contained"
                                color="primary"
                                onClick={handleExportProfile}
                                disabled={exporting || !profile?.id}
                            >
                                {exporting ? 'Exporting...' : 'Export Profile'}
                            </Button>

                            <Button
                                variant="outlined"
                                color="primary"
                                onClick={() => fileInputRef.current?.click()}
                                disabled={importing}
                            >
                                {importing ? 'Importing...' : 'Import Profile'}
                            </Button>
                            <input
                                ref={fileInputRef}
                                type="file"
                                accept=".json"
                                style={{ display: 'none' }}
                                onChange={handleImportProfile}
                            />
                        </Box>
                    </Grid>
                </Grid>
            </Paper>

            <Paper className="section" id="help-settings" elevation={2} style={{ marginTop: '20px' }}>
                <h2>Help</h2>
                <Grid container spacing={2}>
                    <Grid size={12}>
                        <Typography variant="body1" gutterBottom>
                            Need a refresher on how Budgie works?
                        </Typography>
                        <Button
                            variant="contained"
                            color="primary"
                            onClick={() => {
                                localStorage.removeItem('budgie:onboardingCompleted');
                                setShowOnboarding(true);
                            }}
                        >
                            Restart Tutorial
                        </Button>
                    </Grid>
                </Grid>
            </Paper>

            <OnboardingDialog open={showOnboarding} onClose={() => setShowOnboarding(false)} />

            <Snackbar
                open={!!exportImportSnackbar}
                autoHideDuration={4000}
                onClose={() => setExportImportSnackbar('')}
                message={exportImportSnackbar}
            />
        </div>
    );
}
