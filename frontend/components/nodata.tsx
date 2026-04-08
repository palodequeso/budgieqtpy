import { Button, Paper } from '@mui/material';
import * as React from 'react';
import { Link } from 'react-router-dom';

export default function NoData() {
    return (
        <Paper className="section" id="nodata" elevation={2}>
            <h2>Welcome!</h2>

            <p>
                Budgie is a super simple zero-based budgeting app that helps you
                keep track of your monetary-units.
            </p>
            <p>This is NOT an investment tool!</p>
            <p>This is NOT for rich folks!</p>
            <p>
                This is for people who want to factor out some arithmetic, keep
                track of financial needs, and always know what's going on in
                your long-term!
            </p>

            <p>Here is your simple TODO list to make this work...</p>
            <ul>
                <li>
                    Set up your{' '}
                    <Link to="/accounts">
                        <Button variant="text" color="secondary">
                            accounts
                        </Button>
                    </Link>
                </li>
                <li>
                    Set up your{' '}
                    <Link to="/budget">
                        <Button variant="text" color="secondary">
                            budget
                        </Button>
                    </Link>
                </li>
                <li>
                    Run your first budget{' '}
                    <Link to="/">
                        <Button variant="text" color="secondary">
                            extrapolation
                        </Button>
                    </Link>
                </li>
                <li>
                    Don't forget to look through your{' '}
                    <Link to="/profile">
                        <Button variant="text" color="secondary">
                            profile options
                        </Button>
                    </Link>{' '}
                    as well!
                </li>
            </ul>
        </Paper>
    );
}
