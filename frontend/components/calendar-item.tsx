import {
    Alert,
    Button,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    Box,
    Typography,
    Divider
} from '@mui/material';
import * as React from 'react';
import { CalendarEntry } from './calendar-extrapolation';
import CurrencyLabel from './currency-label';
import DateLabel from './date-label';
import MarkPaidDialog from './mark-paid-dialog';

export default function CalendarItem({ entry, profile, close }: { entry: CalendarEntry, profile: any, close: any }) {
    const [markPaidDialogOpen, setMarkPaidDialogOpen] = React.useState(false);
    const [selectedItem, setSelectedItem] = React.useState(null);

    function handleMarkPaidClick(item) {
        setSelectedItem(item);
        setMarkPaidDialogOpen(true);
    }

    function handleMarkPaidClose(refresh?: boolean) {
        setMarkPaidDialogOpen(false);
        setSelectedItem(null);
        if (refresh) {
            close(true); // Close main dialog and refresh schedule
        }
    }

    if (!entry) {
        return null;
    }

    return (
        <>
            <Dialog open={entry !== null} onClose={close} maxWidth="sm" fullWidth>
                <DialogTitle>
                    Schedule Entry - {entry.budget_item?.name}
                </DialogTitle>
                <DialogContent>
                    {/* Entry Summary */}
                    <Box sx={{ 
                        bgcolor: 'background.paper', 
                        p: 2, 
                        borderRadius: 1, 
                        mb: 2,
                        border: 1,
                        borderColor: 'divider'
                    }}>
                        <Typography variant="h6" gutterBottom>
                            {entry.budget_item?.name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            Type: {entry.budget_item?.type}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            Budget Item Amount: <CurrencyLabel amount={entry.budget_item?.amount ?? 0} />
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            Income Date: {entry.income_date ? new Date(entry.income_date).toLocaleDateString() : 'N/A'}
                        </Typography>
                        <Typography variant="body2" color="primary" fontWeight="bold">
                            Entry Total: <CurrencyLabel amount={entry.items.reduce((sum, item) => sum + (item.extrapolation_item?.amount ?? item.amount ?? 0), 0)} />
                        </Typography>
                    </Box>

                    {/* Items Header */}
                    <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                        📋 Scheduled Expenses ({entry.items.length} item{entry.items.length !== 1 ? 's' : ''})
                    </Typography>

                    {/* Items List */}
                    <Box sx={{ mt: 2 }}>
                        {entry.items.map((item, idx) => (
                            <Box
                                key={item.id}
                                sx={{
                                    bgcolor: 'background.paper',
                                    p: 1.5,
                                    mb: 1,
                                    borderRadius: 1,
                                    border: 1,
                                    borderColor: 'divider',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: 1
                                }}
                            >
                                {entry.items.length > 1 && (
                                    <Typography variant="body2" fontWeight="bold" sx={{ minWidth: 30 }}>
                                        #{idx + 1}
                                    </Typography>
                                )}
                                <Box sx={{ minWidth: 110 }}>
                                    <Typography variant="body2" color="text.secondary">
                                        📅 <DateLabel date={item.extrapolation_item?.date || item.date} />
                                    </Typography>
                                </Box>
                                <Box sx={{ minWidth: 100 }}>
                                    <Typography variant="body2" fontWeight="bold">
                                        <CurrencyLabel amount={parseFloat((item.extrapolation_item?.amount ?? item.amount ?? 0).toString())} />
                                    </Typography>
                                </Box>
                                <Box sx={{ flexGrow: 1 }} />
                                {item.ledger_entry && item.ledger_entry.id !== null ? (
                                    <Typography variant="body2" color="success.main" fontWeight="bold">
                                        ✅ Paid
                                    </Typography>
                                ) : (
                                    <Button
                                        variant="contained"
                                        size="small"
                                        onClick={() => handleMarkPaidClick(item)}
                                    >
                                        💳 Mark as Paid
                                    </Button>
                                )}
                            </Box>
                        ))}
                    </Box>
                </DialogContent>
                <DialogActions sx={{ p: 2, bgcolor: 'background.paper' }}>
                    <Button 
                        variant="contained" 
                        onClick={() => close(false)}
                        sx={{ 
                            bgcolor: 'grey.600',
                            color: 'white',
                            '&:hover': {
                                bgcolor: 'grey.700'
                            }
                        }}
                    >
                        ✕ Close
                    </Button>
                </DialogActions>
            </Dialog>

            {/* Mark Paid Dialog */}
            <MarkPaidDialog
                open={markPaidDialogOpen}
                item={selectedItem}
                entry={entry}
                profile={profile}
                onClose={handleMarkPaidClose}
            />
        </>
    );
}
