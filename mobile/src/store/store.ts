import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Types mirror the FastAPI server response shapes
export interface Profile {
  id: number;
  name: string;
  accounts: Account[];
  budget_items: BudgetItem[];
  budget_groups: BudgetGroup[];
}

export interface Account {
  id: number;
  name: string;
  type: string;
  balance: number;
  ledger: LedgerEntry[];
}

interface BudgetItemPeriod {
  id: number | null;
  type: string;
  value: string;
  businessDay: string | null;
}

export interface BudgetItem {
  id: number;
  name: string;
  amount: number;
  type: string;
  budget_group_id: number;
  start_date: string;
  end_date: string;
  periods: BudgetItemPeriod[];
  created_at: string | null;
  updated_at: string | null;
}

export interface LedgerEntry {
  id: number;
  name: string;
  paid_date: string;
  income_date: string;
  type: string;
  amount: number;
  account_id: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface ExtrapolationItem {
  id: number;
  due_date: string;
  amount: number;
  income_date: string | null;
  created_at: string | null;
  updated_at: string | null;
  overridden_at: string | null;
  budget_item_id: number | null;
  ledger_entry_id: number | null;
  category: string | null;
}

interface ColorOverride {
  id: string;
  [key: string]: unknown;
}

export interface BudgetGroup {
  id: number;
  name: string;
}

interface BudgieState {
  // Mobile-only: server connectivity
  serverUrl: string | null;
  setServerUrl: (url: string | null) => void;
  // Theme preference
  themeMode: 'dark' | 'light';
  setThemeMode: (mode: 'dark' | 'light') => void;
  // Mirrors frontend/store.ts slices
  selectedProfileId: number | null;
  setSelectedProfileId: (id: number | null) => void;
  profiles: Profile[];
  setProfiles: (profiles: Profile[]) => void;
  profile: Profile | null;
  setProfile: (profile: Profile | null) => void;
  accounts: Account[];
  setAccounts: (accounts: Account[]) => void;
  budget: BudgetItem[] | null;
  setBudget: (budget: BudgetItem[] | null) => void;
  ledger: LedgerEntry[];
  setLedger: (ledger: LedgerEntry[]) => void;
  extrapolationItems: ExtrapolationItem[];
  setExtrapolationItems: (items: ExtrapolationItem[]) => void;
  colorOverrides: ColorOverride[];
  setColorOverrides: (colorOverrides: ColorOverride[]) => void;
  budgetGroups: BudgetGroup[];
  setBudgetGroups: (budgetGroups: BudgetGroup[]) => void;
  onboardingCompleted: boolean;
  setOnboardingCompleted: (v: boolean) => void;
}

export const useStore = create<BudgieState>()(
  persist(
    (set) => ({
      serverUrl: null,
      setServerUrl: (serverUrl) => set({ serverUrl }),
      themeMode: 'dark' as const,
      setThemeMode: (themeMode) => set({ themeMode }),
      selectedProfileId: null,
      setSelectedProfileId: (selectedProfileId) => set({ selectedProfileId }),
      profiles: [],
      setProfiles: (profiles) => set({ profiles }),
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
      onboardingCompleted: false,
      setOnboardingCompleted: (onboardingCompleted) => set({ onboardingCompleted }),
    }),
    {
      name: 'budgie-config',
      storage: createJSONStorage(() => AsyncStorage),
      partialize: (state) => ({
        serverUrl: state.serverUrl,
        selectedProfileId: state.selectedProfileId,
        themeMode: state.themeMode,
        onboardingCompleted: state.onboardingCompleted,
      }),
    }
  )
);
