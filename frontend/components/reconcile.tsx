import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import {
    Alert, Box, Button, Checkbox, Chip, Grid, MenuItem, Paper, Select,
    Step, StepLabel, Stepper, Table, TableBody, TableCell, TableContainer,
    TableHead, TableRow, TextField, Typography
} from '@mui/material';
import * as React from 'react';
import { useTheme } from '@mui/material/styles';
import { api } from './renderUtils';
import HelpIcon from './help-icon';
import { useStore } from '../store';

interface ParsedTransaction {
    date: string;
    amount: number;
    description: string;
}

interface MatchResult {
    bank_date: string;
    bank_amount: number;
    description: string;
    matched: boolean;
    matched_to: string | null;
    matched_item_id: number | null;
    confidence: number;
}

interface ReviewRow extends MatchResult {
    included: boolean;
    amount_override: number;
    manual_assign_id: number | null;
}

const steps = ['Upload & Parse', 'Match & Review', 'Import'];

export default function Reconcile() {
    const theme = useTheme();
    const profile = useStore((state) => (state as any).profile);
    const accounts = useStore((state) => (state as any).accounts) || [];
    const extrapolationItems = useStore((state) => (state as any).extrapolationItems) || [];

    const [activeStep, setActiveStep] = React.useState(0);
    const [error, setError] = React.useState<string | null>(null);
    const [success, setSuccess] = React.useState<string | null>(null);

    // Step 1 state
    const [fileContent, setFileContent] = React.useState<string>('');
    const [fileName, setFileName] = React.useState<string>('');
    const [accountId, setAccountId] = React.useState<number | ''>('');
    const [dateCol, setDateCol] = React.useState<string>('');
    const [amountCol, setAmountCol] = React.useState<string>('');
    const [descCol, setDescCol] = React.useState<string>('');
    const [parsedTransactions, setParsedTransactions] = React.useState<ParsedTransaction[]>([]);
    const [detectedColumns, setDetectedColumns] = React.useState<string[]>([]);

    // Step 2 state
    const [reviewRows, setReviewRows] = React.useState<ReviewRow[]>([]);

    // Step 3 state
    const [importCount, setImportCount] = React.useState<number | null>(null);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;
        setFileName(file.name);
        const reader = new FileReader();
        reader.onload = (event) => {
            setFileContent(event.target?.result as string);
        };
        reader.readAsText(file);
    };

    const handleParse = async () => {
        try {
            setError(null);
            const payload: any = {
                csv_content: fileContent,
                account_id: accountId,
            };
            if (dateCol) payload.date_col = dateCol;
            if (amountCol) payload.amount_col = amountCol;
            if (descCol) payload.desc_col = descCol;

            const res = await api.post(`/reconcile/${profile.id}/parse`, payload) as any;
            setParsedTransactions(res.transactions || []);
            setDetectedColumns(res.detected_columns || []);
            if (res.date_col) setDateCol(res.date_col);
            if (res.amount_col) setAmountCol(res.amount_col);
            if (res.desc_col) setDescCol(res.desc_col);
            setActiveStep(1);
            handleMatch(res.transactions || []);
        } catch (err) {
            setError(err.message);
        }
    };

    const handleMatch = async (transactions: ParsedTransaction[]) => {
        try {
            setError(null);
            const res = await api.post(`/reconcile/${profile.id}/match`, {
                transactions,
                account_id: accountId,
            }) as any;
            const matches: MatchResult[] = res.matches || [];
            setReviewRows(matches.map((m) => ({
                ...m,
                included: true,
                amount_override: m.bank_amount,
                manual_assign_id: null,
            })));
        } catch (err) {
            setError(err.message);
        }
    };

    const toggleInclude = (idx: number) => {
        setReviewRows((prev) => prev.map((row, i) =>
            i === idx ? { ...row, included: !row.included } : row
        ));
    };

    const rejectMatch = (idx: number) => {
        setReviewRows((prev) => prev.map((row, i) =>
            i === idx ? { ...row, matched: false, matched_to: null, matched_item_id: null, confidence: 0 } : row
        ));
    };

    const setManualAssign = (idx: number, itemId: number) => {
        setReviewRows((prev) => prev.map((row, i) =>
            i === idx ? { ...row, manual_assign_id: itemId } : row
        ));
    };

    const setAmountOverride = (idx: number, amount: number) => {
        setReviewRows((prev) => prev.map((row, i) =>
            i === idx ? { ...row, amount_override: amount } : row
        ));
    };

    const handleImport = async () => {
        try {
            setError(null);
            const items = reviewRows
                .filter((row) => row.included)
                .map((row) => ({
                    bank_date: row.bank_date,
                    amount: row.amount_override,
                    description: row.description,
                    matched_item_id: row.matched_item_id || row.manual_assign_id || null,
                }));

            const res = await api.post(`/reconcile/${profile.id}/import`, {
                items,
                account_id: accountId,
            }) as any;
            setImportCount(res.count || 0);
            setActiveStep(2);
            setSuccess(`Successfully imported ${res.count || 0} transaction(s).`);
        } catch (err) {
            setError(err.message);
        }
    };

    const resetAll = () => {
        setActiveStep(0);
        setError(null);
        setSuccess(null);
        setFileContent('');
        setFileName('');
        setAccountId('');
        setDateCol('');
        setAmountCol('');
        setDescCol('');
        setParsedTransactions([]);
        setDetectedColumns([]);
        setReviewRows([]);
        setImportCount(null);
    };

    const formatCurrency = (val: number) =>
        val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });

    return (
        <Paper className="section" id="reconcile" elevation={2} sx={{ p: 0 }}>
            {/* Title Section */}
            <Box sx={{
                backgroundColor: theme.palette.mode === 'dark' ? '#263238' : '#e0e0e0',
                borderRadius: '8px 8px 0 0',
                padding: '15px 20px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
            }}>
                <Typography variant="h4" sx={{ fontWeight: 'bold', m: 0 }}>
                    Bank Reconciliation
                    <HelpIcon text="Import bank CSV statements and match transactions against your budget to find discrepancies." />
                </Typography>
                {activeStep > 0 && (
                    <Button
                        variant="outlined"
                        color="inherit"
                        sx={{ fontWeight: 'bold' }}
                        onClick={resetAll}
                    >
                        Start Over
                    </Button>
                )}
            </Box>

            {/* Content */}
            <Box sx={{ p: 3 }}>
                {/* Stepper */}
                <Stepper activeStep={activeStep} sx={{ mb: 3 }}>
                    {steps.map((label) => (
                        <Step key={label}>
                            <StepLabel>{label}</StepLabel>
                        </Step>
                    ))}
                </Stepper>

                {error && (
                    <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>
                )}
                {success && (
                    <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>
                )}

                {/* Step 1: Upload & Parse */}
                {activeStep === 0 && (
                    <Box sx={{
                        backgroundColor: theme.palette.mode === 'dark' ? '#37474f' : '#f5f5f5',
                        borderRadius: '8px',
                        padding: '20px',
                    }}>
                        <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 2 }}>
                            Upload Bank Statement
                        </Typography>
                        <Grid container spacing={2}>
                            <Grid size={{ xs: 12, sm: 6 }}>
                                <Typography sx={{ color: '#90a4ae', fontSize: 12, fontWeight: 'bold', mb: 1 }}>
                                    CSV File
                                </Typography>
                                <Button
                                    variant="outlined"
                                    component="label"
                                    fullWidth
                                    sx={{ justifyContent: 'flex-start', textTransform: 'none' }}
                                >
                                    {fileName || 'Choose file...'}
                                    <input
                                        type="file"
                                        accept=".csv"
                                        hidden
                                        onChange={handleFileChange}
                                    />
                                </Button>
                            </Grid>
                            <Grid size={{ xs: 12, sm: 6 }}>
                                <Typography sx={{ color: '#90a4ae', fontSize: 12, fontWeight: 'bold', mb: 1 }}>
                                    Account
                                </Typography>
                                <Select
                                    value={accountId}
                                    onChange={(e) => setAccountId(e.target.value as number)}
                                    fullWidth
                                    size="small"
                                    displayEmpty
                                >
                                    <MenuItem value="" disabled>Select account...</MenuItem>
                                    {accounts.map((acc: any) => (
                                        <MenuItem key={acc.id} value={acc.id}>{acc.name}</MenuItem>
                                    ))}
                                </Select>
                            </Grid>
                            <Grid size={{ xs: 12, sm: 4 }}>
                                <Typography sx={{ color: '#90a4ae', fontSize: 12, fontWeight: 'bold', mb: 1 }}>
                                    Date Column (optional)
                                </Typography>
                                <TextField
                                    placeholder="e.g., Date"
                                    value={dateCol}
                                    onChange={(e) => setDateCol(e.target.value)}
                                    fullWidth
                                    size="small"
                                />
                            </Grid>
                            <Grid size={{ xs: 12, sm: 4 }}>
                                <Typography sx={{ color: '#90a4ae', fontSize: 12, fontWeight: 'bold', mb: 1 }}>
                                    Amount Column (optional)
                                </Typography>
                                <TextField
                                    placeholder="e.g., Amount"
                                    value={amountCol}
                                    onChange={(e) => setAmountCol(e.target.value)}
                                    fullWidth
                                    size="small"
                                />
                            </Grid>
                            <Grid size={{ xs: 12, sm: 4 }}>
                                <Typography sx={{ color: '#90a4ae', fontSize: 12, fontWeight: 'bold', mb: 1 }}>
                                    Description Column (optional)
                                </Typography>
                                <TextField
                                    placeholder="e.g., Description"
                                    value={descCol}
                                    onChange={(e) => setDescCol(e.target.value)}
                                    fullWidth
                                    size="small"
                                />
                            </Grid>
                            <Grid size={12}>
                                <Button
                                    variant="contained"
                                    onClick={handleParse}
                                    disabled={!fileContent || !accountId}
                                    sx={{ fontWeight: 'bold', mt: 1 }}
                                >
                                    Parse
                                </Button>
                            </Grid>
                        </Grid>
                    </Box>
                )}

                {/* Step 2: Match & Review */}
                {activeStep === 1 && (
                    <Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                            <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                                Review Matches
                            </Typography>
                            <Chip
                                label={`${reviewRows.filter((r) => r.matched).length} matched`}
                                color="success"
                                size="small"
                            />
                            <Chip
                                label={`${reviewRows.filter((r) => !r.matched).length} unmatched`}
                                color="warning"
                                size="small"
                            />
                            <Chip
                                label={`${reviewRows.length} total`}
                                size="small"
                            />
                        </Box>

                        <TableContainer>
                            <Table size="small">
                                <TableHead>
                                    <TableRow>
                                        <TableCell sx={{ fontWeight: 'bold' }}>Include</TableCell>
                                        <TableCell sx={{ fontWeight: 'bold' }}>Status</TableCell>
                                        <TableCell sx={{ fontWeight: 'bold' }}>Bank Date</TableCell>
                                        <TableCell sx={{ fontWeight: 'bold' }} align="right">Bank Amount</TableCell>
                                        <TableCell sx={{ fontWeight: 'bold' }}>Description</TableCell>
                                        <TableCell sx={{ fontWeight: 'bold' }}>Matched To</TableCell>
                                        <TableCell sx={{ fontWeight: 'bold' }} align="right">Confidence</TableCell>
                                        <TableCell sx={{ fontWeight: 'bold' }} align="right">Amount Override</TableCell>
                                        <TableCell sx={{ fontWeight: 'bold' }}>Actions</TableCell>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    {reviewRows.length === 0 && (
                                        <TableRow>
                                            <TableCell colSpan={9} align="center" sx={{ py: 4, color: '#90a4ae' }}>
                                                No transactions to review.
                                            </TableCell>
                                        </TableRow>
                                    )}
                                    {reviewRows.map((row, idx) => (
                                        <TableRow key={`review-${idx}`}>
                                            <TableCell>
                                                <Checkbox
                                                    checked={row.included}
                                                    onChange={() => toggleInclude(idx)}
                                                    size="small"
                                                />
                                            </TableCell>
                                            <TableCell>
                                                {row.matched ? (
                                                    <CheckCircleIcon color="success" fontSize="small" />
                                                ) : (
                                                    <HelpOutlineIcon color="warning" fontSize="small" />
                                                )}
                                            </TableCell>
                                            <TableCell>{row.bank_date}</TableCell>
                                            <TableCell align="right">${formatCurrency(row.bank_amount)}</TableCell>
                                            <TableCell>{row.description}</TableCell>
                                            <TableCell>
                                                {row.matched ? (
                                                    row.matched_to
                                                ) : (
                                                    <Select
                                                        value={row.manual_assign_id || ''}
                                                        onChange={(e) => setManualAssign(idx, e.target.value as number)}
                                                        size="small"
                                                        displayEmpty
                                                        sx={{ minWidth: 150 }}
                                                    >
                                                        <MenuItem value="">Standalone</MenuItem>
                                                        {extrapolationItems.map((item: any) => (
                                                            <MenuItem key={item.id} value={item.id}>
                                                                {item.name || item.budget_item_name || `Item ${item.id}`}
                                                            </MenuItem>
                                                        ))}
                                                    </Select>
                                                )}
                                            </TableCell>
                                            <TableCell align="right">
                                                {row.matched ? `${Math.round(row.confidence * 100)}%` : '-'}
                                            </TableCell>
                                            <TableCell align="right">
                                                <TextField
                                                    type="number"
                                                    value={row.amount_override}
                                                    onChange={(e) => setAmountOverride(idx, parseFloat(e.target.value) || 0)}
                                                    size="small"
                                                    sx={{ width: 100 }}
                                                />
                                            </TableCell>
                                            <TableCell>
                                                {row.matched && (
                                                    <Button
                                                        size="small"
                                                        color="warning"
                                                        onClick={() => rejectMatch(idx)}
                                                        sx={{ textTransform: 'none' }}
                                                    >
                                                        Reject
                                                    </Button>
                                                )}
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </TableContainer>

                        <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
                            <Button
                                variant="contained"
                                color="primary"
                                onClick={handleImport}
                                disabled={reviewRows.filter((r) => r.included).length === 0}
                                sx={{ fontWeight: 'bold' }}
                            >
                                Import Selected ({reviewRows.filter((r) => r.included).length})
                            </Button>
                            <Button
                                variant="outlined"
                                onClick={resetAll}
                                sx={{ fontWeight: 'bold' }}
                            >
                                Cancel
                            </Button>
                        </Box>
                    </Box>
                )}

                {/* Step 3: Import Complete */}
                {activeStep === 2 && (
                    <Box sx={{ textAlign: 'center', py: 4 }}>
                        <CheckCircleIcon color="success" sx={{ fontSize: 64, mb: 2 }} />
                        <Typography variant="h5" sx={{ fontWeight: 'bold', mb: 1 }}>
                            Import Complete
                        </Typography>
                        <Typography variant="body1" sx={{ color: '#90a4ae', mb: 3 }}>
                            Successfully imported {importCount} transaction(s).
                        </Typography>
                        <Button
                            variant="contained"
                            onClick={resetAll}
                            sx={{ fontWeight: 'bold' }}
                        >
                            Start New Reconciliation
                        </Button>
                    </Box>
                )}
            </Box>
        </Paper>
    );
}
