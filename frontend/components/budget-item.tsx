import DeleteIcon from '@mui/icons-material/Delete';
import {
    Alert, Autocomplete, Box, Button, Checkbox, Chip, Divider, FormControlLabel,
    Grid,
    IconButton,
    MenuItem, Paper, Select,
    Stack,
    TextField, Typography
} from '@mui/material';
import { LocalizationProvider } from '@mui/x-date-pickers';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { DesktopDatePicker } from '@mui/x-date-pickers/DesktopDatePicker';
import * as React from 'react';
import { useTheme } from '@mui/material/styles';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { api } from './renderUtils';
import { fetchProfile, useStore } from '../store';

const periodData = {
    Daily: [],
    'Business Days': [],
    Weekly: [
        'Monday',
        'Tuesday',
        'Wednesday',
        'Thursday',
        'Friday',
        'Saturday',
        'Sunday',
    ],
    BiWeekly: [
        'Monday',
        'Tuesday',
        'Wednesday',
        'Thursday',
        'Friday',
        'Saturday',
        'Sunday',
    ],
    Monthly: [
        '1st',
        '2nd',
        '3rd',
        '4th',
        '5th',
        '6th',
        '7th',
        '8th',
        '9th',
        '10th',
        '11th',
        '12th',
        '13th',
        '14th',
        '15th',
        '16th',
        '17th',
        '18th',
        '19th',
        '20th',
        '21st',
        '22nd',
        '23rd',
        '24th',
        '25th',
        '26th',
        '27th',
        '28th',
        '29th',
        '30th',
        '31st',
        'Last',
    ],
};

export type PeriodItem = {
    type: string;
    value: string;
    businessDay: string;
    createdAt: string;
    updatedAt: string;
    id?: number;
};

export default function BudgetItem({ budgetItemId = '' }) {
    const theme = useTheme();
    const params = useParams();
    // const navigate = useNavigate();
    const profile = useStore((state) => (state as any).profile);
    const budget = useStore((state) => (state as any).budget);
    const previousBudgetItemGroupNames = useStore((state) => (state as any).budgetGroups || []);

    if (params.budgetItemId) {
        budgetItemId = params.budgetItemId;
    }
    console.log('budgetItemId', budgetItemId);
    console.log('profile.budget', budget);
    const [budgetItem, setBudgetItem] = React.useState<any>(
        budget.find((budgetItem) => budgetItem.id === parseInt(budgetItemId)),
    );

    const [budgetItemName, setBudgetItemName] = React.useState(
        budgetItem?.name || '',
    );
    const [budgetItemType, setBudgetItemType] = React.useState(
        budgetItem?.type || 'expense',
    );
    const [budgetItemAmount, setBudgetItemAmount] = React.useState(
        budgetItem?.amount || 0,
    );
    const [budgetItemGroup, setBudgetItemGroup] = React.useState(budgetItem?.group || '');
    const [budgetItemStartDate, setBudgetItemStartDate] = React.useState(budgetItem?.start_date || new Date);
    const [budgetItemEndDate, setBudgetItemEndDate] = React.useState(budgetItem?.end_date || undefined);
    
    // Check if end date is far in future (no end date)
    const endDateYear = budgetItem?.end_date ? new Date(budgetItem.end_date).getFullYear() : 0;
    const [noEndDate, setNoEndDate] = React.useState(endDateYear > 2100 || !budgetItem?.end_date);
    
    const [budgetItemError, setBudgetItemError] = React.useState('');
    const [periods, setPeriods] = React.useState<PeriodItem[]>(
        budgetItem?.periods || [],
    );
    const [newBudgetItemGroupName, setNewBudgetItemGroupName] = React.useState<string>('');

    const addBudgetItem = async () => {
        try {
            const data = {
                name: budgetItemName,
                type: budgetItemType,
                amount: budgetItemAmount,
                startDate: budgetItemStartDate,
                endDate: noEndDate ? new Date('2999-12-31') : (budgetItemEndDate || new Date()),
                group: budgetItemGroup.id,
                periods,
            };
            if (budgetItem?.id) {
                await api.put(`/budget/${profile.id}/${budgetItem.id}`, data);
            } else {
                await api.post(`/budget/${profile.id}`, data);
            }
            fetchProfile(profile.id);
            // location.pathname = '#/budget';
            // navigate('/budget');
        } catch (err) {
            setBudgetItemError(err.message);
        }
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

    return (
        <Paper className="section" id="budget-item-editor" elevation={2} sx={{ p: 0 }}>
            {/* Header Section */}
            <Box sx={{
                backgroundColor: theme.palette.mode === 'dark' ? '#263238' : '#e0e0e0',
                borderRadius: '8px 8px 0 0',
                padding: '20px',
            }}>
                {/* Back button */}
                <Link to="/budget" style={{ textDecoration: 'none' }}>
                    <Button
                        sx={{
                            mb: 2
                        }}
                    >
                        ⬅️ Back to Budget
                    </Button>
                </Link>

                {/* Title */}
                <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 2 }}>
                    ✏️ {budgetItemId === 'new' ? 'Create' : 'Edit'} Budget Item
                </Typography>
                
                {/* Description */}
                <Typography sx={{ color: '#b0bec5', fontSize: '13px' }}>
                    Budget items are recurring income or expenses that appear in your calendar. Set up when and how often they occur.
                </Typography>
            </Box>

            <Box sx={{ p: 3 }}>
                {budgetItemError && (
                    <Alert severity="error" sx={{ mb: 3 }}>{budgetItemError}</Alert>
                )}
                
                <LocalizationProvider dateAdapter={AdapterDateFns}>
                    <Grid container spacing={3}>
                        {/* Basic Information Section */}
                        <Grid size={12}>
                            <Box sx={{
                                backgroundColor: theme.palette.mode === 'dark' ? '#37474f' : '#f5f5f5',
                                borderRadius: '8px',
                                padding: '20px',
                            }}>
                                <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 2 }}>
                                    📋 Basic Information
                                </Typography>
                                
                                <Box sx={{ mb: 3 }}>
                                    <Typography sx={{ color: '#90a4ae', fontSize: 12, fontWeight: 'bold', mb: 1 }}>
                                        Item Name
                                    </Typography>
                                    <TextField
                                        id="new-budget-item-name"
                                        placeholder="e.g., Rent, Salary, Groceries"
                                        value={budgetItemName}
                                        onChange={(e) => setBudgetItemName(e.target.value)}
                                        fullWidth
                                        size="small"
                                    />
                                </Box>
                                
                                <Box sx={{ mb: 3 }}>
                                    <Typography sx={{ color: '#90a4ae', fontSize: 12, fontWeight: 'bold', mb: 0.5 }}>
                                        Type
                                    </Typography>
                                    <Typography sx={{ color: '#b0bec5', fontSize: 11, fontStyle: 'italic', mb: 1 }}>
                                        Is this money coming in (Income) or going out (Expense)?
                                    </Typography>
                                    <Select
                                        id="new-budget-item-type"
                                        value={budgetItemType}
                                        onChange={(e) => setBudgetItemType(e.target.value)}
                                        fullWidth
                                        size="small"
                                    >
                                        <MenuItem value="income">Income</MenuItem>
                                        <MenuItem value="expense">Expense</MenuItem>
                                    </Select>
                                </Box>
                                
                                <Box>
                                    <Typography sx={{ color: '#90a4ae', fontSize: 12, fontWeight: 'bold', mb: 1 }}>
                                        Amount
                                    </Typography>
                                    <TextField
                                        id="new-budget-item-amount"
                                        type="number"
                                        placeholder="0.00"
                                        onChange={(e) => setBudgetItemAmount(parseFloat(e.target.value))}
                                        value={budgetItemAmount}
                                        fullWidth
                                        size="small"
                                    />
                                </Box>
                            </Box>
                        </Grid>
                        {/* Categorization Section */}
                        <Grid size={12}>
                            <Box sx={{
                                backgroundColor: theme.palette.mode === 'dark' ? '#37474f' : '#f5f5f5',
                                borderRadius: '8px',
                                padding: '20px',
                            }}>
                                <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 1 }}>
                                    📊 Categorization (Optional)
                                </Typography>
                                <Typography sx={{ color: '#b0bec5', fontSize: 11, fontStyle: 'italic', mb: 2 }}>
                                    Group similar items together (e.g., 'Housing', 'Transportation', 'Entertainment')
                                </Typography>
                                
                                <Box sx={{ mb: 2 }}>
                                    {previousBudgetItemGroupNames.map((budgetGroup, index) => (
                                        <Chip
                                            color="primary"
                                            key={`budget-item-group-name-${index}`}
                                            label={budgetGroup.name}
                                            onClick={() => setBudgetItemGroup(budgetGroup)}
                                            variant={budgetGroup.name === budgetItemGroup.name ? 'filled' : 'outlined'}
                                            sx={{ mr: 1, mb: 1 }}
                                        />
                                    ))}
                                </Box>
                                
                                <Box sx={{ display: 'flex', gap: 1 }}>
                                    <TextField
                                        id="new-group-name"
                                        placeholder="Create new group..."
                                        value={newBudgetItemGroupName}
                                        onChange={(e) => setNewBudgetItemGroupName(e.target.value)}
                                        size="small"
                                        sx={{ flex: 1 }}
                                    />
                                    <Button 
                                        onClick={() => addBudgetGroup()}
                                        variant="outlined"
                                        sx={{ whiteSpace: 'nowrap' }}
                                    >
                                        ➕ Add Group
                                    </Button>
                                </Box>
                            </Box>
                        </Grid>
                        {/* Active Period Section */}
                        <Grid size={12}>
                            <Box sx={{
                                backgroundColor: theme.palette.mode === 'dark' ? '#37474f' : '#f5f5f5',
                                borderRadius: '8px',
                                padding: '20px',
                            }}>
                                <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 1 }}>
                                    📅 Active Period
                                </Typography>
                                <Typography sx={{ color: '#b0bec5', fontSize: 11, fontStyle: 'italic', mb: 2 }}>
                                    When should this item be active? For ongoing items, check 'No end date'.
                                </Typography>
                                
                                <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                                    <Box sx={{ flex: 1 }}>
                                        <Typography sx={{ color: '#90a4ae', fontSize: 12, fontWeight: 'bold', mb: 1 }}>
                                            Start Date
                                        </Typography>
                                        <DesktopDatePicker
                                            label="Start Date"
                                            value={budgetItemStartDate ?? new Date()}
                                            onChange={(value) => setBudgetItemStartDate(value as Date)}
                                            slotProps={{ textField: { fullWidth: true, size: 'small' } }}
                                        />
                                    </Box>
                                    <Box sx={{ flex: 1 }}>
                                        <Typography sx={{ color: '#90a4ae', fontSize: 12, fontWeight: 'bold', mb: 1 }}>
                                            End Date
                                        </Typography>
                                        <FormControlLabel
                                            control={
                                                <Checkbox
                                                    checked={noEndDate}
                                                    onChange={(e) => setNoEndDate(e.target.checked)}
                                                    sx={{ color: '#b0bec5' }}
                                                />
                                            }
                                            label="No end date (ongoing)"
                                            sx={{ color: '#b0bec5', fontSize: 12, mb: 1 }}
                                        />
                                        <DesktopDatePicker
                                            label="End Date"
                                            value={budgetItemEndDate ?? new Date(new Date().setFullYear(new Date().getFullYear() + 1))}
                                            onChange={(value) => setBudgetItemEndDate(value as Date)}
                                            disabled={noEndDate}
                                            slotProps={{ textField: { fullWidth: true, size: 'small' } }}
                                        />
                                    </Box>
                                </Box>
                            </Box>
                        </Grid>
                        {/* Recurrence Schedule Section */}
                        <Grid size={12}>
                            <Box sx={{
                                backgroundColor: theme.palette.mode === 'dark' ? '#37474f' : '#f5f5f5',
                                borderRadius: '8px',
                                padding: '20px',
                            }}>
                                <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 1 }}>
                                    🔁 Recurrence Schedule
                                </Typography>
                                
                                <Box sx={{ backgroundColor: theme.palette.mode === 'dark' ? '#263238' : '#e8e8e8', p: 2, borderRadius: 1, mb: 2 }}>
                                    <Typography sx={{ color: '#b0bec5', fontSize: 11, mb: 1 }}>
                                        💡 Define when this item occurs. Examples:
                                    </Typography>
                                    <Typography sx={{ color: '#b0bec5', fontSize: 11 }}>
                                        • Monthly on the 1st: Your rent or mortgage<br />
                                        • BiWeekly on Friday: Paycheck<br />
                                        • Weekly on Monday: Grocery shopping<br />
                                        You can add multiple periods for complex schedules.
                                    </Typography>
                                </Box>
                                
                                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2, px: 1 }}>
                                    <Typography sx={{ flex: 1, fontWeight: 'bold', fontSize: 12 }}>Period Type</Typography>
                                    <Typography sx={{ flex: 1, fontWeight: 'bold', fontSize: 12 }}>Period Value</Typography>
                                    <Typography sx={{ flex: 1, fontWeight: 'bold', fontSize: 12 }}>Business Day</Typography>
                                    <Box sx={{ width: 48 }} />
                                </Box>
                                {periods.map((p, pi) => (
                                    <Box key={`period-${pi}`} sx={{ display: 'flex', gap: 1, mb: 1, alignItems: 'center' }}>
                                        <Select
                                            className="new-budget-item-period-type"
                                            value={p.type}
                                            size="small"
                                            sx={{ flex: 1 }}
                                            onChange={(e) => {
                                                const newPeriods = [...periods];
                                                newPeriods[pi].type = e.target.value;
                                                newPeriods[pi].value = periodData[e.target.value].length
                                                    ? periodData[e.target.value][0]
                                                    : 'Monthly';
                                                setPeriods(newPeriods);
                                            }}
                                        >
                                            {Object.keys(periodData).map((keyName) => (
                                                <MenuItem key={`period-type-entry-${keyName}`} value={keyName}>
                                                    {keyName}
                                                </MenuItem>
                                            ))}
                                        </Select>
                                        
                                        {periodData[p.type] && periodData[p.type].length > 0 && (
                                            <Select
                                                className="new-budget-item-period-item"
                                                value={p.value}
                                                size="small"
                                                sx={{ flex: 1 }}
                                                onChange={(e) => {
                                                    const newPeriods = [...periods];
                                                    newPeriods[pi].value = e.target.value;
                                                    setPeriods(newPeriods);
                                                }}
                                            >
                                                {periodData[p.type]?.map((periodItem) => (
                                                    <MenuItem key={`period-entry-${periodItem}`} value={periodItem}>
                                                        {periodItem}
                                                    </MenuItem>
                                                ))}
                                            </Select>
                                        )}
                                        
                                        <Select
                                            className="new-budget-item-period-business-day"
                                            value={p.businessDay ?? 'none'}
                                            size="small"
                                            sx={{ flex: 1 }}
                                            onChange={(e) => {
                                                const newPeriods = [...periods];
                                                newPeriods[pi].businessDay = e.target.value;
                                                setPeriods(newPeriods);
                                            }}
                                        >
                                            <MenuItem value="none">None</MenuItem>
                                            <MenuItem value="previous">Previous</MenuItem>
                                            <MenuItem value="next">Next</MenuItem>
                                        </Select>
                                        
                                        <IconButton
                                            aria-label="delete"
                                            size="small"
                                            onClick={() => {
                                                setPeriods(periods.filter((_, index) => index !== pi));
                                            }}
                                        >
                                            <DeleteIcon />
                                        </IconButton>
                                    </Box>
                                ))}
                                
                                <Button
                                    onClick={() =>
                                        setPeriods([
                                            ...periods,
                                            {
                                                createdAt: new Date().toISOString(),
                                                updatedAt: new Date().toISOString(),
                                                type: 'Monthly',
                                                value: '1st',
                                                businessDay: 'none',
                                            },
                                        ])
                                    }
                                    variant="outlined"
                                    sx={{ mt: 2 }}
                                >
                                    ➕ Add Another Period
                                </Button>
                            </Box>
                        </Grid>
                        {/* Action Buttons */}
                        <Grid size={12}>
                            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', mt: 2 }}>
                                <Link to="/budget" style={{ textDecoration: 'none' }}>
                                    <Button 
                                        variant="outlined" 
                                        size="large"
                                        sx={{ px: 4, fontWeight: 'bold' }}
                                    >
                                        ❌ Cancel
                                    </Button>
                                </Link>
                                <Button
                                    id="new-budget-submit-button"
                                    variant="contained"
                                    size="large"
                                    onClick={addBudgetItem}
                                    sx={{ px: 4, fontWeight: 'bold' }}
                                >
                                    ✅ {budgetItemId === 'new' ? 'Create' : 'Update'} Budget Item
                                </Button>
                            </Box>
                        </Grid>
                    </Grid>
                </LocalizationProvider>
            </Box>
        </Paper>
    );
}
