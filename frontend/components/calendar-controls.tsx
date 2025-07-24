import {
    Button,
    TextField
} from '@mui/material';
import { DesktopDatePicker, LocalizationProvider } from '@mui/x-date-pickers';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import * as React from 'react';
import CalendarItem from './calendar-item';
import CalendarOneOff from './calendar-one-off';
import CalendarUnscheduled from './calendar-unscheduled';
import CalendarSavingsItems from './calendar-savings-items';
import { useStore } from '../store';
import { api, showSaveDialog } from './renderUtils';
import CalendarExtrapolationConfirmation from './calendar-extrapolation-confirmation';

export default function CalendarControls({
    unscheduledItems,
    extrapolate,
    extrapolation,
    editingCell,
    setEditingCell,
    load,
}) {
    const [unscheduledOpen, setUnscheduledOpen] = React.useState(false);
    const [addingOneOffExpense, setAddingOneOffExpense] = React.useState(false);
    const [addingSavingsItems, setAddingSavingsItems] = React.useState(false);
    const [today, setToday] = React.useState(new Date());
    const [inOneYear, setInOneYear] = React.useState(
        new Date(new Date().setFullYear(new Date().getFullYear() + 1)),
    );
    const [extrapolationModalOpen, setExtrapolationModalOpen] = React.useState(false);
    const profile = useStore((state) => (state as any).profile);

    const download = async () => {
        const { filePath, cancelled } = await showSaveDialog();
        if (cancelled) {
            return;
        }
        await api.post(`/calendar/${profile.id}/downloadspreadsheet`, {
            filePath,
        });
    };

    return (<div>
        <h5>Calendie</h5>
        <LocalizationProvider dateAdapter={AdapterDateFns}>
            <div className="calendar-header">
                <DesktopDatePicker
                    label="Extrapolation From"
                    // inputFormat="MM/dd/yyyy"
                    value={today}
                    onChange={(value) =>
                        setToday(value as Date)
                    }
                    // renderInput={(params) => (
                    //     <TextField {...params} sx={{
                    //         width: '160px',
                    //     }}/>
                    // )}
                />
                <label> - to - </label>
                <DesktopDatePicker
                    label="Extrapolation To"
                    // inputFormat="MM/dd/yyyy"
                    value={inOneYear}
                    onChange={(value) =>
                        setInOneYear(value as Date)
                    }
                    // renderInput={(params) => (
                    //     <TextField {...params} sx={{
                    //         width: '160px',
                    //     }} />
                    // )}
                />
            </div>
        </LocalizationProvider>
        <div>
            <Button 
                style={{ marginRight: '960px' }}
                className="calendar-header-button"
                onClick={() => download()}
                variant="outlined"
                color="secondary"
            >
                Save CSV
                <i className="material-icons">download</i>
            </Button>
            <Button
                id="handle-unscheduled-button"
                variant="contained"
                color="error"
                disabled={unscheduledItems.length === 0}
                onClick={() => setUnscheduledOpen(true)}
                className="calendar-header-button"
                style={{ marginRight: '744px' }}
            >
                {unscheduledItems.length} unscheduled $
                {unscheduledItems
                    .reduce(
                        (acc, item) =>
                            acc +
                            parseFloat((item as any).amount as any),
                        0,
                    )
                    .toFixed(2)}
                <i className="material-icons">warning</i>
            </Button>
            <Button
                id="i-got-paid-button"
                variant="outlined"
                color="secondary"
                // onClick={() => setAddingSavingsItems(true)}
                className="calendar-header-button"
                style={{ marginRight: '604px' }}
                disabled={profile.accounts.find((account) => account.type === 'savings') === undefined}
            >
                I Got Paid
                <i className="material-icons">add</i>
            </Button>
            <Button
                id="add-savings-items"
                variant="outlined"
                color="secondary"
                onClick={() => setAddingSavingsItems(true)}
                className="calendar-header-button"
                style={{ marginRight: '404px' }}
                disabled={profile.accounts.find((account) => account.type === 'savings') === undefined}
            >
                Add Savings Items
                <i className="material-icons">add</i>
            </Button>
            <Button
                id="add-extrapolation-item"
                variant="outlined"
                color="secondary"
                onClick={() => setAddingOneOffExpense(true)}
                className="calendar-header-button"
                style={{ marginRight: '184px' }}
            >
                Add One-Off Expense
                <i className="material-icons">add</i>
            </Button>
            <Button
                id="extrapolate-calendar-button"
                variant="contained"
                color="primary"
                onClick={() => setExtrapolationModalOpen(true)}
                className="calendar-header-button"
            >
                Extrapolate
                <i className="material-icons">arrow_forward</i>
            </Button>
            <CalendarExtrapolationConfirmation
                open={extrapolationModalOpen}
                close={() => setExtrapolationModalOpen(false)}
                extrapolate={extrapolate}
            />
            <CalendarUnscheduled
                profile={profile}
                sortedIncomeDates={Object.keys(extrapolation).sort()}
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
                close={() => {
                    setAddingSavingsItems(false);
                    // if (saved === true) {
                    //     load();
                    // }
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
            />
        </div>
    </div>);
}
