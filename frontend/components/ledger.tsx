import { Alert } from '@mui/material';
import IconButton from '@mui/material/IconButton';
import Paper from '@mui/material/Paper';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import * as React from 'react';
import { Link } from 'react-router-dom';
import CurrencyLabel from './currency-label';
import DateLabel from './date-label';
import { api } from './renderUtils';

export default function Ledger({ profile, account, removeLedgerItem }) {
    const columns: GridColDef[] = [
        { field: 'name', headerName: 'Name', width: 200 },
        { field: 'amount', headerName: 'Amount', width: 130, renderCell: (params) => <CurrencyLabel amount={params.value} />},
        { field: 'type', headerName: 'Type', width: 130 },
        { field: 'updatedAt', headerName: 'Updated', width: 130, renderCell: (params) => <DateLabel date={params.value} />},
        { field: 'account', headerName: 'Start', width: 130, renderCell: (params) => <DateLabel date={params.value} />},
        { field: 'linked', headerName: 'End', width: 130, renderCell: (params) => <DateLabel date={params.value} />},
        { field: 'id', headerName: 'Actions', width: 100, renderCell: (params) => (
            <span>
                <IconButton
                    aria-label="delete"
                    className="delete-budget-item-button"
                    onClick={() => {
                        removeItem(params.value);
                    }}
                >
                    <i className="material-icons">
                        delete
                    </i>
                </IconButton>
                <Link to={`/budget/${params.value}`}>
                    <IconButton
                        aria-label="edit"
                        className="edit-budget-item-button"
                    >
                        <i className="material-icons">
                            edit
                        </i>
                    </IconButton>
                </Link>
            </span>
        )},
    ];

    const [ledgerTableError, setLedgerTableError] = React.useState(null);
    const [ledger, setLedger] = React.useState([]);

    React.useEffect(() => {
        if (!account) {
            return;
        }

        const ledgerEntries: any[] = [];
        account.ledger.forEach((ledgerItem) => {
            ledgerEntries.push({
                ...ledgerItem,
                account: account.name,
            });
        });

        setLedger(ledgerEntries as any);
    }, [account]);

    const removeItem = async (ledgerItemId) => {
        try {
            const json = await api.delete(`/ledger/${profile.id}/${ledgerItemId}`);
            removeLedgerItem({ ...json, id: ledgerItemId });
        } catch (err) {
            setLedgerTableError(err.message);
        }
    };

    return (
        <Paper className="section" id="ledger" elevation={2}>
            <h5>Ledgie</h5>
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
            ></DataGrid>
        </Paper>
    );
}
