import * as React from 'react';
import {
    Box,
    Button,
    Dialog,
    DialogActions,
    DialogContent,
    Typography,
} from '@mui/material';
import { useTheme } from '@mui/material/styles';

const STEPS = [
    {
        title: 'Welcome to Budgie',
        body: "Budgie helps you plan your finances by scheduling bills and income onto a calendar. Here's how to get started.",
    },
    {
        title: 'Create a Profile',
        body: 'Profiles keep budgets separate — one for yourself, one shared with a partner, etc. You can create more anytime from Settings.',
    },
    {
        title: 'Add Your Accounts',
        body: 'Head to the Accounts tab and add your bank accounts (checking, savings, credit cards). These track where your money flows.',
    },
    {
        title: 'Set Up Your Budget',
        body: "In the Budget tab, add your recurring income and expenses. Each item has a schedule — 'monthly on the 1st', 'biweekly on Friday', etc.",
    },
    {
        title: 'Run Extrapolation',
        body: 'Go to the Calendar tab and click Extrapolate. This projects your budget items into the future so you can see what\'s coming.',
    },
    {
        title: "You're Ready!",
        body: 'The calendar is your main workspace. Mark items as paid, add one-off expenses, compute savings, and hide past pay periods as you go.',
    },
];

interface OnboardingDialogProps {
    open: boolean;
    onClose: () => void;
}

export default function OnboardingDialog({ open, onClose }: OnboardingDialogProps) {
    const [step, setStep] = React.useState(0);
    const theme = useTheme();

    const finish = () => {
        localStorage.setItem('budgie:onboardingCompleted', 'true');
        setStep(0);
        onClose();
    };

    const isLast = step === STEPS.length - 1;

    return (
        <Dialog open={open} onClose={finish} maxWidth="sm" fullWidth>
            <DialogContent sx={{ textAlign: 'center', pt: 4, pb: 2 }}>
                {/* Step dots */}
                <Box sx={{ display: 'flex', justifyContent: 'center', gap: 1, mb: 3 }}>
                    {STEPS.map((_, i) => (
                        <Box
                            key={i}
                            sx={{
                                width: 10,
                                height: 10,
                                borderRadius: '50%',
                                backgroundColor: i === step
                                    ? theme.palette.primary.main
                                    : theme.palette.action.disabled,
                                transition: 'background-color 0.2s',
                            }}
                        />
                    ))}
                </Box>

                <Typography variant="h5" sx={{ fontWeight: 'bold', mb: 2 }}>
                    {STEPS[step].title}
                </Typography>

                <Typography
                    variant="body1"
                    sx={{
                        color: theme.palette.text.secondary,
                        lineHeight: 1.8,
                        maxWidth: 400,
                        mx: 'auto',
                    }}
                >
                    {STEPS[step].body}
                </Typography>
            </DialogContent>

            <DialogActions sx={{ justifyContent: 'space-between', px: 3, pb: 2 }}>
                <Button
                    onClick={() => setStep((s) => s - 1)}
                    disabled={step === 0}
                    sx={{ visibility: step === 0 ? 'hidden' : 'visible' }}
                >
                    Back
                </Button>

                <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button onClick={finish} color="inherit" sx={{ opacity: 0.6 }}>
                        Skip
                    </Button>
                    <Button
                        variant="contained"
                        onClick={isLast ? finish : () => setStep((s) => s + 1)}
                    >
                        {isLast ? 'Get Started' : 'Next'}
                    </Button>
                </Box>
            </DialogActions>
        </Dialog>
    );
}
