import * as React from 'react';
import Account from '../../components/account';
import { fireEvent, render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { BrowserRouter as Router } from 'react-router-dom';
import { act } from 'react-dom/test-utils';
import { useStore } from '../../store';

expect.extend(toHaveNoViolations);

function setup(accounts: {}[] = [], accountId = '') {
    useStore.setState({ profile: { accounts, }, accounts, });
    const { container } = render(
        <Router>
            <Account accountId={accountId} />
        </Router>,
    );
    return { container };
}

let rejects = false;
let request = { url: '', method: '', body: {} };
beforeAll(() => {
    global.fetch = jest.fn((url: string, opts: any) => {
        request.url = url;
        request.method = opts.method;
        request.body = opts.body;
        return Promise.resolve({
            json: () => {
                if (rejects) {
                    return Promise.reject('doom');
                }
                return Promise.resolve(
                    JSON.stringify({ id: 1, ledger: [], ...request.body }),
                );
            },
        });
    }) as jest.Mock;
});

afterAll(() => {
    jest.clearAllMocks();
});

test('account pass axe', async () => {
    const { container } = setup();
    expect(await axe(container)).toHaveNoViolations();
});

test('account can render without a ledger', () => {
    setup(
        [
            {
                id: 1,
                name: 'checking-test',
                balance: 100,
                type: 'checking',
                ledger: [],
            },
        ],
        '1',
    );

    const checking = screen.getByDisplayValue('checking-test');
    expect(checking !== null).toBe(true);
});

test('account can render with a ledger', () => {
    setup(
        [
            {
                id: 1,
                name: 'checking-test',
                balance: 100,
                type: 'checking',
                ledger: [
                    {
                        id: 1,
                        name: 'test',
                        amount: 100,
                        type: 'income',
                        date: '2020-01-01',
                        createdAt: '2020-01-01',
                        updatedAt: '2020-01-01',
                    },
                ],
            },
        ],
        '1',
    );

    const checking = screen.getByDisplayValue('checking-test');
    expect(checking !== null).toBe(true);
});

test('can validate and create a new account', async () => {
    setup([], 'new');

    const submit = screen.getByText('Save');
    expect(submit).toBeDefined();
    act(() => {
        fireEvent.click(submit);
    });

    screen.getByTestId('account-type');
    const name = screen.getByLabelText('Account Name');
    const balance = screen.getByLabelText('Account Balance');

    await act(async () => {
        fireEvent.change(name, { target: { value: 'checking-test' } });
        fireEvent.change(balance, { target: { value: '100' } });
        fireEvent.click(submit);
    });
});

test('can update an account', async () => {
    setup(
        [
            {
                id: 1,
                name: 'checking-test',
                balance: 100,
                type: 'checking',
                ledger: [
                    {
                        id: 1,
                        name: 'test',
                        amount: 100,
                        type: 'income',
                        date: '2020-01-01',
                        createdAt: '2020-01-01',
                        updatedAt: '2020-01-01',
                    },
                ],
            },
        ],
        '1',
    );

    const submit = screen.getByText('Save');
    expect(submit).toBeDefined();
    const name = screen.getByLabelText('Account Name');
    const balance = screen.getByLabelText('Account Balance');

    await act(async () => {
        fireEvent.change(name, { target: { value: 'checking-test-updated' } });
        fireEvent.change(balance, { target: { value: '1001' } });
        fireEvent.click(submit);
    });
});
