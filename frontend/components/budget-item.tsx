import DeleteIcon from '@mui/icons-material/Delete';
import {
    Alert, Autocomplete, Button, Chip, FormControlLabel,
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
    const params = useParams();
    // const navigate = useNavigate();
    const profile = useStore((state) => (state as any).profile);

    if (params.budgetItemId) {
        budgetItemId = params.budgetItemId;
    }
    const [budgetItem, setBudgetItem] = React.useState<any>(
        profile.budget.find((budgetItem) => budgetItem.id === parseInt(budgetItemId)),
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
    const [budgetItemStartDate, setBudgetItemStartDate] = React.useState(budgetItem?.startDate || new Date);
    const [budgetItemEndDate, setBudgetItemEndDate] = React.useState(budgetItem?.endDate || undefined);
    const [budgetItemError, setBudgetItemError] = React.useState('');
    const [periods, setPeriods] = React.useState<PeriodItem[]>(
        budgetItem?.periods || [],
    );
    const previousBudgetItemGroupNames = useStore((state) => (state as any).profile.budgetGroups);
    const [newBudgetItemGroupName, setNewBudgetItemGroupName] = React.useState<string>('');

    const addBudgetItem = async () => {
        try {
            const data = {
                name: budgetItemName,
                type: budgetItemType,
                amount: budgetItemAmount,
                startDate: budgetItemStartDate,
                endDate: budgetItemEndDate || null,
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
        <Paper className="section" id="budget-item-editor" elevation={2}>
            <h2>Budget Item</h2>
            {budgetItemError && (
                <Alert severity="error">{budgetItemError}</Alert>
            )}
            <LocalizationProvider dateAdapter={AdapterDateFns}>
                <Grid
                    container
                    spacing={2}
                    sx={{ marginTop: '4px', marginBottom: '4px' }}
                >
                    <Grid size={12}>
                        <FormControlLabel
                            control={
                                <TextField
                                    label="Name"
                                    id="new-budget-item-name"
                                    value={budgetItemName}
                                    onChange={(e) => setBudgetItemName(e.target.value)}
                                    sx={{ marginLeft: '8px' }}
                                />
                            }
                            label="Budget Item Name"
                            labelPlacement="start"
                            sx={{ marginRight: '4px' }}
                        />
                    </Grid>
                    <Grid size={12}>
                        <FormControlLabel
                            control={
                                <Select
                                    id="new-budget-item-type"
                                    type="text"
                                    value={budgetItemType}
                                    inputProps={{
                                        'aria-label': 'budget item type',
                                    }}
                                    onChange={(e) =>
                                        setBudgetItemType(e.target.value)
                                    }
                                    sx={{ marginLeft: '8px' }}
                                >
                                    <MenuItem value="income">Income</MenuItem>
                                    <MenuItem value="expense">Expense</MenuItem>
                                </Select>
                            }
                            label="Budget Item Type"
                            labelPlacement="start"
                            sx={{ marginRight: '4px' }}
                        />
                    </Grid>
                    <Grid size={12}>
                        <FormControlLabel
                            control={
                                <TextField
                                    id="new-budget-item-amount"
                                    type="number"
                                    onChange={(e) =>
                                        setBudgetItemAmount(parseFloat(e.target.value))
                                    }
                                    value={budgetItemAmount}
                                    sx={{ marginLeft: '8px' }}
                                />
                            }
                            label="Budget Item Amount"
                            labelPlacement="start"
                            sx={{ marginRight: '4px', display: 'inline-block' }}
                        />
                        <Typography sx={{display: 'inline-block'}}>
                            {budgetItemName} {budgetItemType} of amount {budgetItemType === 'income' ? '+' : '-'}${budgetItemAmount}
                        </Typography>
                    </Grid>
                    <Grid size={12}>
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
                    </Grid>
                    <Grid size={12}>
                        {/* <div style={{marginTop: '8px', marginBottom: '8px'}}> */}
                            {previousBudgetItemGroupNames.map((budgetGroup, index) => (
                                <Chip
                                    color="secondary"
                                    key={`budget-item-group-name-${index}`}
                                    label={budgetGroup.name}
                                    onClick={() => setBudgetItemGroup(budgetGroup)}
                                    variant={budgetGroup.name === budgetItemGroup.name ? 'filled' : 'outlined'}
                                    sx={{ marginLeft: '8px' }}
                                />
                            ))}
                        {/* </div> */}
                    </Grid>
                    <Grid size={12}>
                        <DesktopDatePicker
                            label="Start Date"
                            // inputFormat="MM/dd/yyyy"
                            value={budgetItemStartDate ?? new Date()}
                            onChange={(value) =>
                                setBudgetItemStartDate(value as Date)
                            }
                            // renderInput={(params) => (
                            //     <TextField {...params} />
                            // )}
                        />
                        <label> - to - </label>
                        <DesktopDatePicker
                            label="End Date"
                            // inputFormat="MM/dd/yyyy"
                            value={budgetItemEndDate ?? null}
                            onChange={(value) =>
                                setBudgetItemEndDate(value as Date)
                            }
                            // renderInput={(params) => (
                            //     <TextField {...params} />
                            // )}
                        />
                    </Grid>
                    <Grid size={12}>
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
                            color="primary"
                            variant="contained"
                            sx={{ float: 'right' }}
                        >
                            Add Budget Item Schedule Period
                            <i className="material-icons">add</i>
                        </Button>
                    </Grid>
                    <Grid size={4}>
                        <Typography>Period Type</Typography>
                    </Grid>
                    <Grid size={4}>
                        <Typography>Period Value</Typography>
                    </Grid>
                    <Grid size={4}>
                        <Typography>Business Day</Typography>
                    </Grid>
                    {periods.map((p, pi) => (<Grid sx={{ margin: '2px', marginLeft: '4px' }} container spacing={2} key={`period-${pi}`}>
                        <Grid size={4}>
                            <Select
                                className="new-budget-item-period-type"
                                label="Schedule Type"
                                type="text"
                                value={p.type}
                                fullWidth
                                onChange={(e) => {
                                    const newPeriods = [...periods];
                                    newPeriods[pi].type = e.target.value;
                                    newPeriods[pi].value = periodData[
                                        e.target.value
                                    ].length
                                        ? periodData[e.target.value][0]
                                        : 'Monthly';
                                    setPeriods(newPeriods);
                                }}
                            >
                                {Object.keys(periodData).map((keyName) => {
                                    return (
                                        <MenuItem
                                            key={`period-type-entry-${keyName}`}
                                            value={keyName}
                                        >
                                            {keyName}
                                        </MenuItem>
                                    );
                                })}
                            </Select>
                        </Grid>
                        <Grid size={4}>
                            {periodData[p.type] && periodData[p.type].length > 0 && (
                                <Select
                                    className="new-budget-item-period-item"
                                    label="Schedule Item"
                                    type="text"
                                    value={p.value}
                                    fullWidth
                                    onChange={(e) => {
                                        const newPeriods = [...periods];
                                        newPeriods[pi].value = e.target.value;
                                        setPeriods(newPeriods);
                                    }}
                                >
                                    {periodData[p.type]?.map((periodItem) => {
                                        return (
                                            <MenuItem
                                                key={`period-entry-${periodItem}`}
                                                value={periodItem}
                                            >
                                                {periodItem}
                                            </MenuItem>
                                        );
                                    }) ?? null}
                                </Select>
                            )}
                        </Grid>
                        <Grid size={3}>
                            <Select
                                className="new-budget-item-period-business-day"
                                inputProps={{ 'aria-label': 'business day' }}
                                type="text"
                                fullWidth
                                value={p.businessDay ?? 'none'}
                                onChange={(e) => {
                                    const newPeriods = [...periods];
                                    newPeriods[pi].businessDay =
                                        e.target.value;
                                    setPeriods(newPeriods);
                                }}
                            >
                                <MenuItem value="none">None</MenuItem>
                                <MenuItem value="previous">
                                    Previous
                                </MenuItem>
                                <MenuItem value="next">Next</MenuItem>
                            </Select>
                        </Grid>
                        <Grid size={1}>
                            <IconButton
                                aria-label="delete"
                                onClick={() => {
                                    setPeriods(
                                        periods.filter((_, index) => index !== pi),
                                    );
                                }}
                            >
                                <DeleteIcon />
                            </IconButton>
                        </Grid>
                    </Grid>))}
                </Grid>
            </LocalizationProvider>
            <div>
                <Link to="/budget">
                    <Button color="secondary" variant="outlined">
                        Cancel
                    </Button>
                </Link>
                <Button
                    id="new-budget-submit-button"
                    variant="contained"
                    onClick={addBudgetItem}
                >
                    Save
                    <i className="material-icons">save</i>
                </Button>
            </div>
        </Paper>
    );
}
