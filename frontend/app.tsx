import * as React from 'react';
import { HashRouter, Route, Routes } from "react-router-dom";

import Header from './components/header';
import Accounts from './components/accounts';
import Budget from './components/budget';
import Calendar from './components/calendar';

import { api } from './components/renderUtils';
import Profile from './components/profile';
import Settings from './components/settings';
import Account from './components/account';
import BudgetItem from './components/budget-item';
import LedgerItem from './components/ledger-item';
import Profiles from './components/profiles';

import { useStore, fetchProfile } from './store';

export default function App(props) {
    const { swapTheme } = props;
    const profileId = useStore((state) => (state as any).selectedProfileId);
    const setProfileId = useStore((state) => (state as any).setSelectedProfileId);
    const profile = useStore((state) => (state as any).profile);

    const theme = localStorage.getItem('budgie:theme');

    React.useEffect(() => {
        console.log('use effect app profileId', profileId);
        if (profileId) {
            fetchProfile(profileId.toString());
        }
    }, [ profileId ]);

    const logout = () => {
        localStorage.removeItem('budgie:profileId');
        setProfileId(0);
        // Profile state will automatically update via useStore when setProfileId is called
    }

    return (<div id="app">
        { profile !== null ? (<HashRouter>
            <Header profile={profile} logout={logout} />
            <Routes>
                <Route path="/" element={<Calendar />} />
                <Route path="/calendar" element={<Calendar />} />
                <Route path="/accounts" element={<Accounts /> } />
                <Route path="/accounts/:accountId" element={<Account /> } />
                <Route path="/budget" element={<Budget />} />
                <Route path="/budget/:budgetItemId" element={<BudgetItem />} />
                <Route path="/ledger/:ledgerItemId" element={<LedgerItem />} />
                <Route path="/profile" element={<Profile theme={theme} swapTheme={swapTheme} />} />
                <Route path="/settings" element={<Settings theme={theme} swapTheme={swapTheme} />} />
            </Routes>
        </HashRouter>) : (<Profiles />) }
    </div>);
}
