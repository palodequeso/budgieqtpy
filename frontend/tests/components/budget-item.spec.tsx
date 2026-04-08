import * as React from 'react';
import BudgetItem from '../../components/budget-item';
import {
    act,
    fireEvent,
    render,
    screen,
    waitFor,
    queryByAltText,
    queryByAttribute,
} from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { BrowserRouter as Router } from 'react-router-dom';
import { useStore } from '../../store';

expect.extend(toHaveNoViolations);

const request = {
    url: '',
    method: '',
    body: {},
};

let isOpen = true;
let addData;
function setup(budget = [], budgetItemId = '') {
    useStore.setState({ profile: { budget, budgetGroups: [{id: 0, name: 'test'}], }, budget, });
    const { container } = render(<Router>
        <BudgetItem
            budgetItemId={budgetItemId}
        />,
    </Router>);
    return {
        container,
    };
}

let rejects = false;
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
                return Promise.resolve(true);
            },
        });
    }) as jest.Mock;
});

afterAll(() => {
    jest.clearAllMocks();
});

test('budget pass axe', async () => {
    const { container } = setup();
    expect(await axe(container)).toHaveNoViolations();
});

test('budget can render a budget item', async () => {
    setup([{
        id: 1,
        name: 'test',
        amount: 100,
        type: 'expense',
        periods: [{ type: 'Monthly', value: '1st' }],
        createdAt: new Date(),
        updatedAt: new Date(),
    }] as any, '1');

    const name = screen.getByLabelText('Name');
    expect(name).toBeDefined();

    jest.restoreAllMocks();
});

test('budget can save a budget item', async () => {
    const { container } = setup([{
        id: 1,
        name: 'test',
        amount: 100,
        type: 'expense',
        periods: [{ type: 'Monthly', value: '1st' }],
        createdAt: new Date(),
        updatedAt: new Date(),
    }] as any, '1');

    const saveButton = queryByAttribute('id', container, 'new-budget-submit-button');
    expect(saveButton).toBeDefined();
    if (saveButton) {
        saveButton.click();
    }

    jest.restoreAllMocks();
});

test('budget can add a budget item', async () => {
    const { container } = setup([{
        name: 'test',
        amount: 100,
        type: 'expense',
        periods: [{ type: 'Monthly', value: '1st' }],
        createdAt: new Date(),
        updatedAt: new Date(),
    }] as any, '1');

    const saveButton = queryByAttribute('id', container, 'new-budget-submit-button');
    expect(saveButton).toBeDefined();
    if (saveButton) {
        saveButton.click();
    }

    jest.restoreAllMocks();
});
