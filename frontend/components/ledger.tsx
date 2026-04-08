import { Alert, Box, Button } from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import * as React from 'react';
import { Link } from 'react-router-dom';
import { useTheme } from '@mui/material/styles';
import CurrencyLabel from './currency-label';
import DateLabel from './date-label';
import { api } from './renderUtils';

export default function Ledger({ profile, account, removeLedgerItem }) {
    const theme = useTheme();
    
    const columns: GridColDef[] = [
        { field: 'id', headerName: 'ID', width: 80 },
        { field: 'name', headerName: 'Name', width: 200 },
        { field: 'paidDate', headerName: 'Paid Date', width: 130, renderCell: (params) => <DateLabel date={params.value} />},
        { field: 'incomeDate', headerName: 'Income Date', width: 130, renderCell: (params) => <DateLabel date={params.value} />},
        { field: 'type', headerName: 'Type', width: 100 },
        { field: 'amount', headerName: 'Amount', width: 130, renderCell: (params) => <CurrencyLabel amount={params.value} />},
        { field: 'createdAt', headerName: 'Created', width: 130, renderCell: (params) => <DateLabel date={params.value} />},
        { field: 'updatedAt', headerName: 'Updated', width: 130, renderCell: (params) => <DateLabel date={params.value} />},
        { field: 'actions', headerName: 'Actions', width: 180, renderCell: (params) => (
            <Box sx={{ display: 'flex', gap: 1 }}>
                <Link to={`/ledger/${params.row.id}`} style={{ textDecoration: 'none' }}>
                    <Button
                        variant="contained"
                        size="small"
                        sx={{
                            backgroundColor: '#1976d2',
                            color: 'white',
                            fontSize: '11px',
                            padding: '6px 12px',
                            minWidth: 'auto',
                            '&:hover': {
                                backgroundColor: '#1565c0',
                            }
                        }}
                    >
                        ✏️ Edit
                    </Button>
                </Link>
                <Button
                    variant="contained"
                    size="small"
                    onClick={() => removeItem(params.row.id)}
                    sx={{
                        backgroundColor: '#d32f2f',
                        color: 'white',
                        fontSize: '11px',
                        padding: '6px 12px',
                        minWidth: 'auto',
                        '&:hover': {
                            backgroundColor: '#b71c1c',
                        }
                    }}
                >
                    🗑️ Delete
                </Button>
            </Box>
        )},
    ];

    const [ledgerTableError, setLedgerTableError] = React.useState(null);
    const [ledger, setLedger] = React.useState([]);

    React.useEffect(() => {
        if (!account) {
            return;
        }

        const ledgerEntries: any[] = [];
        // Handle case where ledger might be undefined or null
        if (account.ledger && Array.isArray(account.ledger)) {
            account.ledger.forEach((ledgerItem) => {
                ledgerEntries.push({
                    ...ledgerItem,
                    account: account.name,
                });
            });
        }

        setLedger(ledgerEntries as any);
    }, [account]);

    const removeItem = async (ledgerItemId) => {
        const ledgerItem = ledger.find(item => item.id === ledgerItemId);
        const itemName = ledgerItem?.name || 'this ledger entry';
        
        if (!window.confirm(`Are you sure you want to delete '${itemName}'?\n\nThis action cannot be undone.`)) {
            return;
        }
        
        try {
            const json = await api.delete(`/ledger/${profile.id}/${ledgerItemId}`);
            removeLedgerItem({ ...json, id: ledgerItemId });
        } catch (err) {
            setLedgerTableError(err.message);
        }
    };

    return (
        <Box sx={{
            backgroundColor: theme.palette.mode === 'dark' ? '#37474f' : '#f5f5f5',
            border: `2px solid ${theme.palette.mode === 'dark' ? '#546e7a' : '#90a4ae'}`,
            borderRadius: '8px',
            overflow: 'hidden'
        }}>
            {ledgerTableError && <Alert severity="error">{ledgerTableError}</Alert>}
            <DataGrid
                pageSizeOptions={[10, 25, 50, 100]}
                initialState={{
                  pagination: {
                    paginationModel: {
                      pageSize: 10,
                    },
                  },
                }}
                rows={ledger}
                columns={columns}
                sx={{
                    border: 'none',
                    '& .MuiDataGrid-columnHeaders': {
                        backgroundColor: theme.palette.mode === 'dark' ? '#263238' : '#e0e0e0',
                        color: theme.palette.mode === 'dark' ? 'white' : 'black',
                        fontWeight: 'bold',
                        fontSize: '12px',
                    },
                    '& .MuiDataGrid-cell': {
                        padding: '8px',
                        color: theme.palette.mode === 'dark' ? 'white' : 'black',
                    },
                    '& .MuiDataGrid-row:hover': {
                        backgroundColor: theme.palette.mode === 'dark' ? 'rgba(25, 118, 210, 0.12)' : 'rgba(25, 118, 210, 0.08)',
                    },
                }}
            />
        </Box>
    );
}
