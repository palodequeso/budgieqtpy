import * as React from 'react';
import Accounts from '../../components/accounts';
import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { BrowserRouter as Router } from 'react-router-dom';
import { useStore } from '../../store';

expect.extend(toHaveNoViolations);

function setup(accounts: {}[] = []) {
    useStore.setState({ profile: { accounts, }, accounts, });
    const { container } = render(
        <Router>
            <Accounts />
        </Router>,
    );
    return { container };
}

test('accounts pass axe', async () => {
    const { container } = setup();
    expect(await axe(container)).toHaveNoViolations();
});

test('accounts can render accounts', () => {
    setup([{
        id: 1,
        name: 'checking-test',
        balance: 100,
        type: 'checking',
        ledger: [],
    }, {
        id: 2,
        name: 'savings-test',
        balance: 1000,
        type: 'savings',
        ledger: [],
    }]);

    const checking = screen.getByText('Account: checking-test');
    expect(checking !== null).toBe(true);

    const savings = screen.getByText('Account: savings-test');
    expect(savings !== null).toBe(true);
});
