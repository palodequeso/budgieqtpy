import * as React from 'react';
import LedgerItem from '../../components/ledger-item';
import {
    act,
    fireEvent,
    queryByAttribute,
    render,
    screen,
    waitFor,
} from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { BrowserRouter as Router } from 'react-router-dom';
import { useStore } from '../../store';

expect.extend(toHaveNoViolations);

function setup(budget = [], ledgerItemId = '', accountId = '1') {
    useStore.setState({ profile: {
        id: 1,
        budget,
        accounts: [],
    } });
    const { container } = render(<Router>
        <LedgerItem
            ledgerItemId={ledgerItemId}
        />,
    </Router>);
    return {
        container,
    };
}

test('ledger pass axe', async () => {
    const { container } = setup();
    expect(await axe(container)).toHaveNoViolations();
});

test('can render a ledger item', async () => {
    setup([{
        id: 1,
        name: 'test',
        amount: 100,
        type: 'income',
        periods: [{
            id: 1,
            type: 'Monthly',
            value: '1st',
            businessDay: 'none',
        }],
    }] as any, '1');

    const name = screen.getByLabelText('Name');
    expect(name).toBeDefined();

    jest.restoreAllMocks();
});

test('can change a ledger item budget item', async () => {
    const { container } = setup([{
        id: 1,
        name: 'test',
        amount: 100,
        type: 'income',
        periods: [{
            id: 1,
            type: 'Monthly',
            value: '1st',
            businessDay: 'none',
        }],
    }, {
        id: 2,
        name: 'test2',
        amount: -10,
        type: 'expense',
        periods: [{
            id: 1,
            type: 'Monthly',
            value: '1st',
            businessDay: 'none',
        }],
    }] as any, '1');

    await act(async () => {
        const budgetItemSelect = queryByAttribute('data-testid', container, 'new-ledger-item-budget-item');
        expect(budgetItemSelect).toBeDefined();
        if (budgetItemSelect) {
            fireEvent.click(budgetItemSelect);
        }
    });
    jest.restoreAllMocks();
});


test('can save a ledger item', async () => {
    const { container } = setup([{
        id: 1,
        name: 'test',
        amount: 100,
        type: 'income',
        periods: [{
            id: 1,
            type: 'Monthly',
            value: '1st',
            businessDay: 'none',
        }],
    }] as any, '1');

    await act(async () => {
        const saveButton = queryByAttribute('data-testid', container, 'new-ledger-item-submit');
        expect(saveButton).toBeDefined();
        if (saveButton) {
            fireEvent.click(saveButton);
        }
    });
    jest.restoreAllMocks();
});
