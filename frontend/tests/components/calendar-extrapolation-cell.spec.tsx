import {
    render,
    screen
} from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import * as React from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import { CalendarEntry } from '../../components/calendar-extrapolation';
import CalendarExtrapolationCell from '../../components/calendar-extrapolation-cell';

expect.extend(toHaveNoViolations);

let callEntry;

function setup() {
    const { container } = render(<Router>
        <table><tbody><tr>
        <CalendarExtrapolationCell
            entry={{
                incomeDate: '2020-01-01',
                budgetItem: {
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
                },
                items: [],
                amount: 100,
            } as CalendarEntry}
            date={'2020-01-01'}
            theme={'dark'}
            extrapolation={{}}
            setEditingCell={(entry) => {
                callEntry = entry;
            }}
        />
        </tr></tbody></table>,
    </Router>);
    return {
        container,
    };
}

test('calendar extrapolation cell pass axe', async () => {
    const { container } = setup();
    expect(await axe(container)).toHaveNoViolations();
});

test('can render an extrapolation cell', async () => {
    setup();
    const name = screen.getAllByText('$100.00')[0];
    expect(name).toBeDefined();
    name.click();
    expect(callEntry).toBeDefined();
    jest.restoreAllMocks();
});
