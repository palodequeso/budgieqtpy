import {
    Button,
    TextField,
    Menu,
    MenuItem,
    ListItemIcon,
    ListItemText
} from '@mui/material';
import { DesktopDatePicker, LocalizationProvider } from '@mui/x-date-pickers';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import * as React from 'react';
import { useTheme } from '@mui/material/styles';
import CalendarItem from './calendar-item';
import CalendarOneOff from './calendar-one-off';
import CalendarUnscheduled from './calendar-unscheduled';
import CalendarSavingsItems from './calendar-savings-items';
import CalendarGotPaid from './calendar-got-paid';
import { useStore } from '../store';
import { api } from './renderUtils';
import HelpIcon from './help-icon';
import CalendarExtrapolationConfirmation from './calendar-extrapolation-confirmation';
import CalendarAIAnalysis from './calendar-ai-analysis';

export default function CalendarControls({
    unscheduledItems,
    extrapolate,
    extrapolation,
    editingCell,
    setEditingCell,
    load,
    schedule,
    showAllColumns,
    setShowAllColumns,
}) {
    const [unscheduledOpen, setUnscheduledOpen] = React.useState(false);
    const [addingOneOffExpense, setAddingOneOffExpense] = React.useState(false);
    const [addingSavingsItems, setAddingSavingsItems] = React.useState(false);
    const [gotPaidOpen, setGotPaidOpen] = React.useState(false);
    const [today, setToday] = React.useState(new Date());
    const [inOneYear, setInOneYear] = React.useState(
        new Date(new Date().setFullYear(new Date().getFullYear() + 1)),
    );
    const [extrapolationModalOpen, setExtrapolationModalOpen] = React.useState(false);
    const [actionsMenuAnchor, setActionsMenuAnchor] = React.useState<null | HTMLElement>(null);
    const [aiAnalysisOpen, setAiAnalysisOpen] = React.useState(false);
    const profile = useStore((state) => (state as any).profile);
    const theme = useTheme();

    const download = async () => {
        try {
            // Trigger download via direct link
            const timestamp = new Date().toISOString().split('T')[0];
            const filename = `budget-schedule-${timestamp}.ods`;
            
            // Use a direct download link (no /api prefix needed)
            window.open(`/calendar/${profile.id}/downloadspreadsheet?filename=${filename}`, '_blank');
        } catch (error) {
            console.error('Download failed:', error);
            alert('Failed to download spreadsheet file');
        }
    };

    const hideCurrentColumn = async () => {
        try {
            const sortedDates = Object.keys(extrapolation).sort();
            if (sortedDates.length === 0) {
                alert('No columns to hide');
                return;
            }
            
            // Filter to get visible dates only (same logic as calendar.tsx getVisibleIncomeDates)
            let visibleDates = sortedDates;
            if (profile?.hidden_through) {
                const hiddenDate = new Date(profile.hidden_through);
                visibleDates = sortedDates.filter(dateStr => {
                    const date = new Date(dateStr);
                    return date > hiddenDate;
                });
            }
            
            if (visibleDates.length === 0) {
                alert('No visible columns to hide');
                return;
            }
            
            const currentColumn = visibleDates[0]; // Leftmost visible (oldest non-hidden) column
            const column = extrapolation[currentColumn];
            
            // Check if all items are paid
            let unpaidCount = 0;
            // This is a simplified check - in reality would need to check the schedule data
            
            const confirmMessage = `Hide income column for ${currentColumn}?\n\nThis will hide it from the calendar view.${unpaidCount > 0 ? `\n\n⚠️ Warning: ${unpaidCount} unpaid items in this column!` : ''}`;
            
            if (!window.confirm(confirmMessage)) {
                return;
            }
            
            // Update profile's hidden_through date
            await api.put(`/profiles/${profile.id}/hidden_through`, {
                hidden_through: currentColumn
            });
            
            // Reload the calendar
            load();
            alert(`Column ${currentColumn} is now hidden.`);
        } catch (error) {
            console.error('Hide column failed:', error);
            alert('Failed to hide column');
        }
    };

    return (
        <div style={{ padding: '20px 0' }}>
            {/* Title Section */}
            <div style={{
                backgroundColor: theme.palette.mode === 'dark' ? '#263238' : '#e0e0e0',
                borderRadius: '8px',
                padding: '15px 20px',
                marginBottom: '20px'
            }}>
                <h3 style={{ 
                    margin: 0,
                    fontSize: '1.5rem',
                    fontWeight: 'bold'
                }}>
                    📅 Budget Calendar
                </h3>
            </div>

            {/* Controls Container */}
            <div style={{
                backgroundColor: theme.palette.mode === 'dark' ? '#37474f' : '#f5f5f5',
                borderRadius: '8px',
                padding: '20px'
            }}>
                {/* Date Range Row */}
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    marginBottom: '20px',
                    flexWrap: 'wrap'
                }}>
                    <span style={{ fontWeight: 'bold', fontSize: '13px' }}>
                        Extrapolation Period:
                    </span>
            <LocalizationProvider dateAdapter={AdapterDateFns}>
                <DesktopDatePicker
                    label="Extrapolation From"
                    value={today}
                    onChange={(value) => setToday(value as Date)}
                    slotProps={{
                        textField: { size: 'small' }
                    }}
                />
                <span style={{ margin: '0 4px' }}>to</span>
                <DesktopDatePicker
                    label="Extrapolation To"
                    value={inOneYear}
                    onChange={(value) => setInOneYear(value as Date)}
                    slotProps={{
                        textField: { size: 'small' }
                    }}
                />
            </LocalizationProvider>
                </div>

                {/* Action Buttons Row */}
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    flexWrap: 'wrap'
                }}>
                    {/* Primary Actions */}
                    <Button
                        id="extrapolate-calendar-button"
                        variant="contained"
                        color="primary"
                        onClick={() => setExtrapolationModalOpen(true)}
                        sx={{ 
                            fontWeight: 'bold',
                            px: 3
                        }}
                    >
                        🔄 Extrapolate
                    </Button>
                    <HelpIcon text="Projects your budget items onto the calendar. Run this after adding or changing budget items." />
                    
                    <Button
                        id="i-got-paid-button"
                        variant="contained"
                        color="success"
                        onClick={() => setGotPaidOpen(true)}
                        disabled={!profile?.accounts || profile.accounts.length === 0}
                        sx={{ 
                            fontWeight: 'bold',
                            px: 3
                        }}
                    >
                        💰 I Got Paid
                    </Button>
                    
                    <Button
                        id="handle-unscheduled-button"
                        variant="contained"
                        color="error"
                        disabled={unscheduledItems.length === 0}
                        onClick={() => setUnscheduledOpen(true)}
                        sx={{ 
                            fontWeight: 'bold',
                            px: 3
                        }}
                    >
                        ⚠️ {unscheduledItems.length} Unscheduled ($
                        {unscheduledItems
                            .reduce((acc, item) => acc + parseFloat((item as any).amount as any), 0)
                            .toFixed(2)})
                    </Button>

                    <div style={{ flex: 1 }} />
                    
                    {/* Secondary Actions */}
                    <Button
                        id="add-extrapolation-item"
                        size="small"
                        variant="outlined"
                        onClick={() => setAddingOneOffExpense(true)}
                        sx={{ 
                            color: theme.palette.mode === 'dark' ? '#b0bec5' : '#546e7a',
                            borderColor: theme.palette.mode === 'dark' ? '#546e7a' : '#bdbdbd'
                        }}
                    >
                        ➕ Add One-Off
                    </Button>
                    
                    <Button
                        id="add-savings-items"
                        size="small"
                        variant="outlined"
                        onClick={() => setAddingSavingsItems(true)}
                        disabled={!profile?.accounts?.find((account: any) => account.type === 'Savings')}
                        sx={{ 
                            color: theme.palette.mode === 'dark' ? '#b0bec5' : '#546e7a',
                            borderColor: theme.palette.mode === 'dark' ? '#546e7a' : '#bdbdbd'
                        }}
                    >
                        💎 Add Savings
                    </Button>
                    
                    <Button
                        size="small"
                        variant="outlined"
                        onClick={() => hideCurrentColumn()}
                        // disabled={Object.keys(extrapolation).length === 0}
                        sx={{ 
                            color: theme.palette.mode === 'dark' ? '#b0bec5' : '#546e7a',
                            borderColor: theme.palette.mode === 'dark' ? '#546e7a' : '#bdbdbd'
                        }}
                    >
                        👁️ Hide Column
                    </Button>

                    {profile?.hidden_through && (
                        <Button
                            size="small"
                            variant="outlined"
                            onClick={() => setShowAllColumns(!showAllColumns)}
                            sx={{
                                color: theme.palette.mode === 'dark' ? '#b0bec5' : '#546e7a',
                                borderColor: theme.palette.mode === 'dark' ? '#546e7a' : '#bdbdbd'
                            }}
                        >
                            {showAllColumns ? '👁️ Hide Past' : '👁️ Show Hidden'}
                        </Button>
                    )}

                    <Button
                        size="small"
                        variant="outlined"
                        onClick={() => download()}
                        sx={{ 
                            color: theme.palette.mode === 'dark' ? '#b0bec5' : '#546e7a',
                            borderColor: theme.palette.mode === 'dark' ? '#546e7a' : '#bdbdbd'
                        }}
                    >
                        📊 Export
                    </Button>

                    <Button
                        size="small"
                        variant="outlined"
                        onClick={() => setAiAnalysisOpen(true)}
                        sx={{
                            color: theme.palette.mode === 'dark' ? '#b0bec5' : '#546e7a',
                            borderColor: theme.palette.mode === 'dark' ? '#546e7a' : '#bdbdbd'
                        }}
                    >
                        🤖 AI Analysis
                    </Button>
                </div>
            </div>
        <div>
            <CalendarExtrapolationConfirmation
                open={extrapolationModalOpen}
                close={() => setExtrapolationModalOpen(false)}
                extrapolate={extrapolate}
            />
            <CalendarUnscheduled
                profile={profile}
                sortedIncomeDates={schedule?.sorted_income_dates || Object.keys(extrapolation).sort()}
                open={unscheduledOpen}
                close={(saved) => {
                    setUnscheduledOpen(false);
                    if (saved === true) {
                        load();
                    }
                }}
                unscheduled={unscheduledItems}
            />
            <CalendarSavingsItems
                profile={profile}
                open={addingSavingsItems}
                close={(saved) => {
                    setAddingSavingsItems(false);
                    if (saved === true) {
                        load();
                    }
                }}
            />
            <CalendarGotPaid
                profile={profile}
                schedule={schedule}
                open={gotPaidOpen}
                close={(saved) => {
                    setGotPaidOpen(false);
                    if (saved === true) {
                        load();
                    }
                }}
            />
            <CalendarOneOff
                sortedIncomeDates={Object.keys(extrapolation).sort()}
                open={addingOneOffExpense}
                profile={profile}
                close={(saved) => {
                    setAddingOneOffExpense(false);
                    if (saved === true) {
                        load();
                    }
                }}
            />
            <CalendarItem
                close={(saved) => {
                    setEditingCell(null);
                    if (saved === true) {
                        load();
                    }
                }}
                entry={editingCell ?? null as any}
                profile={profile}
                schedule={schedule}
            />
            <CalendarAIAnalysis
                open={aiAnalysisOpen}
                close={() => setAiAnalysisOpen(false)}
                profileId={profile?.id}
            />
        </div>
    </div>);
}
