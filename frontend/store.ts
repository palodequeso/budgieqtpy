import { create } from 'zustand';
import { api } from './components/renderUtils';

export const useStore = create((set) => ({
    profile: null,
    setProfile: (profile) => set({ profile }),
    accounts: [],
    setAccounts: (accounts) => set({ accounts }),
    budget: null,
    setBudget: (budget) => set({ budget }),
    ledger: [],
    setLedger: (ledger) => set({ ledger }),
    extrapolationItems: [],
    setExtrapolationItems: (extrapolationItems) => set({ extrapolationItems }),
    colorOverrides: [],
    setColorOverrides: (colorOverrides) => set({ colorOverrides }),
    budgetGroups: [],
    setBudgetGroups: (budgetGroups) => set({ budgetGroups }),
    setAll: (profile, accounts, budget, ledger, extrapolationItems, colorOverrides) => {
        set({
            profile,
            accounts,
            budget,
            ledger,
            extrapolationItems,
            colorOverrides,
        });
    },
    setFromProfile: (profile) => {
        set({
            accounts: profile.accounts,
            budget: profile.budget,
            colorOverrides: profile.colorOverrides,
        });
    },
    profiles: [],
    setProfiles: (profiles) => set({ profiles }),
    selectedProfileId: localStorage.getItem('budgie:profileId') ?? null,
    setSelectedProfileId: (selectedProfileId) => set({ selectedProfileId }),
}));

export function fetchProfile(profileId: string | null = null) {
    profileId = profileId ? profileId : localStorage.getItem('budgie:profileId');
    if (profileId) {
        localStorage.setItem('budgie:profileId', profileId);
        console.log('fetchProfile profileId', profileId);
        api.get(`/profiles/${profileId}`).then(json => {
            const res = json as any;
            console.log('res', res);
            // console.log('profile fetch response', res);
            if (res) {
                const profile = res;
                console.log('fetchProfile profile fetched', profile);
                useStore.setState({
                    profile,
                    accounts: profile.accounts,
                    budget: profile.budget_items,
                    // colorOverrides: profile.colorOverrides,
                    // budgetGroups: profile.budgetGroups,
                });
            }
        });
    }
}

export function fetchProfiles() {
    api.get('/profiles').then(json => {
        const res = json as any;
        // console.log('profiles fetch response', res);
        if (res.length > 0) {
            useStore.setState({ profiles: res });
        }
    });
}
