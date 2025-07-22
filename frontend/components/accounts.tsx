import {
    Box,
    Card,
    CardContent,
    CardHeader,
    Grid,
    Typography,
} from '@mui/material';
import Button from '@mui/material/Button';
import Paper from '@mui/material/Paper';
import * as React from 'react';
import { Link } from 'react-router-dom';
import CurrencyLabel from './currency-label';
import { useStore } from '../store';

export default function Accounts() {
    const accounts = useStore((state) => (state as any).accounts);

    return (
        <Paper className="section" id="accounts" elevation={2}>
            <h2>Accounts</h2>
            <Link to="/accounts/new">
                <Button
                    className="add-account-button"
                    variant="contained"
                    color="primary"
                >
                    Add Account
                    <i className="material-icons">add</i>
                </Button>
            </Link>
            <Box>
                {accounts.map((account) => (
                    <Card
                        variant="outlined"
                        key={account.id}
                        sx={{ marginBottom: 4 }}
                    >
                        <CardHeader
                            title={`Account: ${account.name}`}
                            action={
                                <Link to={`/accounts/${account.id}`}>
                                    <Button
                                        aria-label="settings"
                                        color="secondary"
                                    >
                                        View/Edit
                                        <i className="material-icons">edit</i>
                                    </Button>
                                </Link>
                            }
                        />
                        <CardContent>
                            <Grid container spacing={2}>
                                <Grid size={12}>
                                    <Typography
                                        sx={{ fontSize: 14 }}
                                        color="text.secondary"
                                        gutterBottom
                                    >
                                        Type
                                    </Typography>
                                </Grid>
                                <Grid size={12}>
                                    <Typography variant="h5" component="div">
                                        {account.account_type.toLowerCase()}
                                    </Typography>
                                </Grid>
                                <Grid size={12}>
                                    <Typography
                                        sx={{ fontSize: 14 }}
                                        color="text.secondary"
                                        gutterBottom
                                    >
                                        Balance
                                    </Typography>
                                </Grid>
                                <Grid size={12}>
                                    <Typography variant="h5" component="div">
                                        <CurrencyLabel amount={account.balance} />
                                    </Typography>
                                </Grid>
                                <Grid size={12}>
                                    <Typography
                                        sx={{ fontSize: 14 }}
                                        color="text.secondary"
                                        gutterBottom
                                    >
                                        Ledger Entries
                                    </Typography>
                                </Grid>
                                <Grid size={12}>
                                    <Typography variant="h5" component="div">
                                        {account?.ledger?.length > 0
                                            ? account.ledger.length.toString() +
                                              ' ledger entries for this account'
                                            : 'No ledger entries for this account'}
                                    </Typography>
                                </Grid>
                            </Grid>
                        </CardContent>
                    </Card>
                ))}
            </Box>
        </Paper>
    );
}
