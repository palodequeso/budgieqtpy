import * as React from 'react';
import Ledger from '../../components/ledger';
import {
    act,
    fireEvent,
    render,
    screen,
    waitFor,
} from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { BrowserRouter as Router } from 'react-router-dom';
import { useStore } from '../../store';

expect.extend(toHaveNoViolations);

const testAccount = {
    id: 1,
    name: 'checking-test',
    balance: 100,
    type: 'checking',
    ledger: [
        {
            id: 1,
            type: 'expense',
            name: 'test',
            createdAt: '2020-01-01',
            accountId: 1,
            amount: 100,
            budgetItem: null,
            extrapolationItem: null,
        },
        {
            id: 2,
            type: 'expense',
            name: 'test2',
            createdAt: '2020-01-01',
            accountId: 1,
            amount: 200,
            budgetItem: null,
            extrapolationItem: { id: 4 },
        },
    ],
};

function setup(
    account: {} = {
        ledger: [],
    },
    budget: [] = [],
) {
    useStore.setState({ profile: {
        id: 1,
        accounts: [account],
        budget,
    } });
    const removeLedgerItem = jest.fn();
    const profile = {
        id: 1,
        accounts: [account],
        budget,
    };
    const { container } = render(
        <Router>
            <Ledger
                profile={profile}
                account={account}
                removeLedgerItem={removeLedgerItem}
            />
            ,
        </Router>,
    );
    return { container, removeLedgerItem };
}

test('ledger pass axe', async () => {
    const { container } = setup();
    expect(await axe(container)).toHaveNoViolations();
});

test('ledger can render ledger items', async () => {
    setup(testAccount);

    const txt3 = screen.getAllByText('checking-test');
    expect(txt3 !== null).toBe(true);

    const txt4 = screen.getByText('test');
    expect(txt4 !== null).toBe(true);

    const txt5 = screen.getByText('test2');
    expect(txt5 !== null).toBe(true);
});

test('ledger can fail delete a ledger entry', async () => {
    setup(testAccount);
    global.fetch = jest.fn((url, req) => {
        return Promise.reject(new Error('test error'));
    }) as any;

    await act(() => {
        fireEvent.click(
            document.querySelector('.ledger-item-delete-button') as any,
        );
    });

    jest.restoreAllMocks();
});
