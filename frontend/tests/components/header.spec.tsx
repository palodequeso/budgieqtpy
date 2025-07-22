import * as React from 'react';
import Header from '../../components/header';
import { act, render, screen, fireEvent, waitFor } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { BrowserRouter as Router } from 'react-router-dom';

expect.extend(toHaveNoViolations);

function setup() {
    const logout = jest.fn();
    const { container } = render(<Router>
        <Header logout={logout} />
    </Router>);
    return { container, logout };
}

test('header pass axe', async () => {
    const { container } = setup();
    expect(await axe(container)).toHaveNoViolations();
});

test('Header renders correctly', () => {
    const { logout } = setup();
    const txt = screen.getByText('Budgie');
    expect(txt !== null).toBe(true);

    const link = screen.getByText('Accounts');
    expect(link !== null).toBe(true);

    const logoutButton = screen.getByText('Switch Profile');
    expect(logoutButton !== null).toBe(true);
    act(() => {
        fireEvent.click(logoutButton);
    });
    expect(logout).toHaveBeenCalledTimes(1);
});
