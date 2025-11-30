import AppBar from '@mui/material/AppBar';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import * as React from 'react';
import { Link } from 'react-router-dom';

const navLinks = [
    { title: 'Calendar', path: '/' },
    { title: 'Accounts', path: '/accounts' },
    { title: 'Budget', path: '/budget' },
    { title: 'Profile', path: '/profile' },
    { title: 'Settings', path: '/settings' },
];

export default function Header(props) {
    return (
        <Box sx={{ flexGrow: 1 }}>
            <AppBar position="static" color="primary">
                <Toolbar>
                    <Typography
                        variant="h6"
                        component="div"
                        sx={{ marginRight: '16px' }}
                    >
                        Budgie
                    </Typography>
                    {navLinks.map((link) => (
                        <Link to={link.path} key={link.path}>
                            <Button variant="text" color="info">
                                {link.title}
                            </Button>
                        </Link>
                    ))}
                    <div style={{ flexGrow: 1 }} />
                    <Button color="inherit" onClick={props.logout}>
                        Switch Profile
                    </Button>
                </Toolbar>
            </AppBar>
        </Box>
    );
}
