import { Divider, Box, Card, CardContent, Typography, Container } from '@mui/material';
import Button from '@mui/material/Button';
import Paper from '@mui/material/Paper';
import TextField from '@mui/material/TextField';
import * as React from 'react';
import { useTheme } from '@mui/material/styles';
import { api } from './renderUtils';
import { fetchProfiles, useStore } from '../store';

export default function Profiles() {
    const theme = useTheme();
    const [newProfileName, setNewProfileName] = React.useState<string>('');
    const profiles = useStore((state) => (state as any).profiles);
    const setProfiles = useStore((state) => (state as any).setProfiles);
    const setSelectedProfileId = useStore((state) => (state as any).setSelectedProfileId);

    React.useEffect(() => {
        fetchProfiles();
    }, []);

    const createProfile = async () => {
        if (!newProfileName) {
            return;
        }

        const res = await api.post('/profiles', { name: newProfileName, });
        setProfiles([...profiles, res]); // not needed because fetch probably
        setNewProfileName('');
        fetchProfiles();
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            createProfile();
        }
    };

    return (
        <Container maxWidth="md" sx={{ py: 8 }}>
            <Paper id="profiles-form" elevation={4} sx={{ p: 4 }}>
                {/* Welcome Section */}
                <Box sx={{ 
                    textAlign: 'center', 
                    mb: 6,
                    p: 4,
                    backgroundColor: theme.palette.mode === 'dark' ? '#263238' : '#e0e0e0',
                    borderRadius: 2
                }}>
                    <Typography variant="h2" component="h1" gutterBottom sx={{ 
                        fontWeight: 'bold',
                        fontSize: '3rem',
                        mb: 2
                    }}>
                        🐦 Budgie
                    </Typography>
                    <Typography variant="h5" sx={{ 
                        color: '#90a4ae',
                        mb: 2,
                        fontWeight: 500
                    }}>
                        Your Personal Budget Calendar
                    </Typography>
                    <Typography variant="body1" sx={{ 
                        color: '#b0bec5',
                        maxWidth: '600px',
                        margin: '0 auto',
                        lineHeight: 1.8
                    }}>
                        Budgie helps you plan and track your budget over time.
                        Schedule recurring expenses, track income, and see your financial future.
                    </Typography>
                </Box>

                {/* Profiles Section */}
                {profiles.length > 0 && (
                    <Box sx={{ mb: 5 }}>
                        <Typography variant="h5" component="h2" gutterBottom sx={{ 
                            textAlign: 'center',
                            fontWeight: 'bold',
                            mb: 3
                        }}>
                            Select Your Profile
                        </Typography>
                        <Box sx={{ 
                            display: 'flex', 
                            gap: 2, 
                            flexWrap: 'wrap',
                            justifyContent: 'center'
                        }}>
                            {profiles.map((profile) => (
                                <Card 
                                    key={profile.id}
                                    sx={{ 
                                        minWidth: 180,
                                        minHeight: 120,
                                        cursor: 'pointer',
                                        transition: 'all 0.3s ease',
                                        backgroundColor: theme.palette.mode === 'dark' ? '#37474f' : '#f5f5f5',
                                        border: theme.palette.mode === 'dark' ? '2px solid #546e7a' : '2px solid #bdbdbd',
                                        '&:hover': {
                                            backgroundColor: theme.palette.mode === 'dark' ? '#455a64' : '#eeeeee',
                                            borderColor: '#1976d2',
                                            transform: 'translateY(-4px)',
                                            boxShadow: 4
                                        }
                                    }}
                                    onClick={() => setSelectedProfileId(profile.id)}
                                >
                                    <CardContent sx={{ 
                                        display: 'flex', 
                                        alignItems: 'center', 
                                        justifyContent: 'center',
                                        height: '100%'
                                    }}>
                                        <Typography variant="h6" sx={{ 
                                            color: 'white',
                                            fontWeight: 'bold',
                                            textAlign: 'center'
                                        }}>
                                            {profile.name}
                                        </Typography>
                                    </CardContent>
                                </Card>
                            ))}
                        </Box>
                    </Box>
                )}

                <Divider sx={{ my: 4 }} />

                {/* Create Profile Section */}
                <Box>
                    <Typography variant="h5" component="h2" gutterBottom sx={{ 
                        textAlign: 'center',
                        fontWeight: 'bold',
                        mb: 3
                    }}>
                        Create New Profile
                    </Typography>
                    <Box sx={{ 
                        display: 'flex', 
                        gap: 2, 
                        justifyContent: 'center',
                        alignItems: 'center',
                        flexWrap: 'wrap'
                    }}>
                        <TextField
                            id="name"
                            label="Profile Name"
                            placeholder="Enter profile name..."
                            value={newProfileName}
                            onChange={(e) => setNewProfileName(e.target.value)}
                            onKeyPress={handleKeyPress}
                            variant="outlined"
                            sx={{ minWidth: 250 }}
                        />
                        <Button
                            variant="contained"
                            color="primary"
                            size="large"
                            onClick={() => createProfile()}
                            disabled={!newProfileName}
                            sx={{ 
                                px: 4,
                                fontWeight: 'bold'
                            }}
                        >
                            Create Profile
                        </Button>
                    </Box>
                </Box>
            </Paper>
        </Container>
    );
}
