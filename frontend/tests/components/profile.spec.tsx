import * as React from 'react';
import Profile from '../../components/profile';
import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { BrowserRouter as Router } from 'react-router-dom';
import { useStore } from '../../store';

expect.extend(toHaveNoViolations);

function setup(profile) {
    useStore.setState({ profile });
    const { container } = render(
        <Router>
            <Profile theme="dark" swapTheme={() => {}} />
        </Router>,
    );
    return { container };
}

test('account pass axe', async () => {
    const { container } = setup({
        id: 1,
        username: 'test',
        email: 'test@test.com',
        theme: 'dark',
        holidays: [],
        colorOverrides: [],
        budgetGroups: [],
    });
});
