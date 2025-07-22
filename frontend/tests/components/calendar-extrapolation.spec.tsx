import {
    render,
    screen
} from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import * as React from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import CalendarExtrapolation, { CalendarEntry, CalendarIncomeColumn } from '../../components/calendar-extrapolation';

expect.extend(toHaveNoViolations);

let callEntry;

function setup() {
    const { container } = render(<Router>
        <table>
        <CalendarExtrapolation
            miscEntries={[]}
            miscRowCount={0}
            theme={'dark'}
            extrapolation={{
                '2020-01-01': CalendarIncomeColumn.fromData(
                    '2020-01-01',
                    [{
                        incomeDate: '2020-01-01',
                        budgetItem: { id: 1, name: 'test', type: 'expense', amount: 10, },
                        items: [{ id: 1, name: 'test', amount: 10 }],
                        amount: -10,
                    } as CalendarEntry],
                    0,
                    {
                        incomeDate: '2020-01-01',
                        budgetItem: { id: 2, name: 'test', type: 'income', amount: 100, },
                        items: [{ id: 2, name: 'test', amount: 100 }],
                        amount: 100,
                    } as CalendarEntry,
                ),
            }}
            setEditingCell={(entry) => {
                callEntry = entry;
            }}
        />
        </table>,
    </Router>);
    return {
        container,
    };
}

test('calendar extrapolation pass axe', async () => {
    const { container } = setup();
    expect(await axe(container)).toHaveNoViolations();
});

test('can render an extrapolation', async () => {
    setup();
    const amount = screen.getAllByText('-$10.00')[0];
    expect(amount).toBeDefined();
    jest.restoreAllMocks();
});
