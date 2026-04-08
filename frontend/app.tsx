import * as React from 'react';
import { HashRouter, Route, Routes } from "react-router-dom";

import Header from './components/header';
import Accounts from './components/accounts';
import Budget from './components/budget';
import Calendar from './components/calendar';
import Dashboard from './components/dashboard';

import { api } from './components/renderUtils';
import Profile from './components/profile';
import Settings from './components/settings';
import Account from './components/account';
import BudgetItem from './components/budget-item';
import Debts from './components/debts';
import Reconcile from './components/reconcile';
import LedgerItem from './components/ledger-item';
import Profiles from './components/profiles';

import { useStore, fetchProfile } from './store';
import OnboardingDialog from './components/onboarding';

export default function App(props) {
    const { swapTheme } = props;
    const profileId = useStore((state) => (state as any).selectedProfileId);
    const setProfileId = useStore((state) => (state as any).setSelectedProfileId);
    const profile = useStore((state) => (state as any).profile);

    const theme = localStorage.getItem('budgie:theme');
    const [showOnboarding, setShowOnboarding] = React.useState(
        () => localStorage.getItem('budgie:onboardingCompleted') !== 'true'
    );

    React.useEffect(() => {
        if (profileId) {
            fetchProfile(profileId.toString());
        }
    }, [ profileId ]);

    const logout = () => {
        setProfileId(null);
        useStore.setState({ profile: null, accounts: [], budget: null, ledger: [], extrapolationItems: [] });
    }

    return (<div id="app">
        { profile !== null ? (<HashRouter>
            <OnboardingDialog open={showOnboarding} onClose={() => setShowOnboarding(false)} />
            <Header profile={profile} logout={logout} />
            <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/calendar" element={<Calendar />} />
                <Route path="/accounts" element={<Accounts /> } />
                <Route path="/accounts/:accountId" element={<Account /> } />
                <Route path="/budget" element={<Budget />} />
                <Route path="/budget/:budgetItemId" element={<BudgetItem />} />
                <Route path="/debts" element={<Debts />} />
                <Route path="/reconcile" element={<Reconcile />} />
                <Route path="/ledger/:ledgerItemId" element={<LedgerItem />} />
                <Route path="/profile" element={<Profile theme={theme} swapTheme={swapTheme} />} />
                <Route path="/settings" element={<Settings theme={theme} swapTheme={swapTheme} />} />
            </Routes>
        </HashRouter>) : (<Profiles />) }
    </div>);
}
