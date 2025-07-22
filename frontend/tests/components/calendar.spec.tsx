import * as React from 'react';
import Calendar from '../../components/calendar';
import { render, screen } from '@testing-library/react';
import { BrowserRouter as Router } from 'react-router-dom';
import { axe, toHaveNoViolations } from 'jest-axe';
import { act } from 'react-dom/test-utils';
import { calendarLoad } from './testdata';
import { useStore } from '../../store';

expect.extend(toHaveNoViolations);

beforeAll(() => {
    global.window.ResizeObserver = jest.fn(() => ({
        observe: jest.fn(),
        unobserve: jest.fn(),
        disconnect: jest.fn(),
    })) as jest.Mock;
    global.fetch = jest.fn(() => Promise.resolve({ json: () => Promise.resolve(calendarLoad) })) as jest.Mock;
});

afterAll(() => {
    jest.clearAllMocks();
});

function setup(profile = { accounts: [], budget: [] }) {
    useStore.setState({ profile });
    const { container } = render(<Router><Calendar /></Router>);
    return {
        container,
    };
}

test('calendar pass axe', async () => {
    let axeResults;
    await act(async () => {
        const { container } = setup();
        axeResults = await axe(container);
    });
    expect(axeResults).toHaveNoViolations();
});
