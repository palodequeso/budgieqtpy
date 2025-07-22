import { Divider } from '@mui/material';
import Button from '@mui/material/Button';
import Paper from '@mui/material/Paper';
import TextField from '@mui/material/TextField';
import * as React from 'react';
import { api } from './renderUtils';
import { fetchProfiles, useStore } from '../store';

export default function Profiles() {
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

    return (
        <Paper id="profiles-form" elevation={2}>
            <h2>Budgie</h2>
            <div>
                <h2>Select a profile</h2>
                <div>
                    {profiles.map((profile) => (
                        <Button
                            key={profile.id}
                            variant="outlined"
                            color="primary"
                            onClick={() => {
                                setSelectedProfileId(profile.id);
                            }}
                        >
                            {profile.name}
                        </Button>
                    ))}
                </div>
            </div>
            <Divider />
            <form>
                <h2>or, Create a profile...</h2>
                <div className="login-form-field">
                    <TextField
                        id="name"
                        label="name"
                        value={newProfileName}
                        onChange={(e) => setNewProfileName(e.target.value)}
                    />
                    &nbsp;&nbsp;&nbsp;&nbsp;
                    <Button
                        variant="outlined"
                        color="primary"
                        onClick={() => createProfile()}
                    >
                        Create
                    </Button>
                </div>
            </form>
        </Paper>
    );
}
