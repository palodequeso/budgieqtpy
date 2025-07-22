import * as React from 'react';
import Budget from '../../components/budget';
import { act, fireEvent, render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { BrowserRouter as Router } from 'react-router-dom';
import { useStore } from '../../store';

expect.extend(toHaveNoViolations);

function setup(budget: {}[] = []) {
    useStore.setState({ profile: { budget, }, budget, });
    const removeBudgetItem = jest.fn();
    const { container } = render(
        <Router>
            <Budget />
        </Router>
    );
    return { container, removeBudgetItem };
}

test('budget pass axe', async () => {
    const { container } = setup();
    expect(await axe(container)).toHaveNoViolations();
});

test('budget can render budget items', async () => {
    setup([
        {
            id: 1,
            name: 'test',
            amount: 100,
            periods: [{ type: 'Monthly', value: '1' }],
        },
        {
            id: 2,
            name: 'test2',
            amount: 200,
            periods: [{ type: 'Monthly', value: '2' }],
        },
    ]);

    const txt = screen.getByText('test');
    expect(txt !== null).toBe(true);

    const txt2 = screen.getByText('test2');
    expect(txt2 !== null).toBe(true);
});
