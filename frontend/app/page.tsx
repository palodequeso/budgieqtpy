// frontend/app/page.tsx
"use client";

import { useState, useEffect } from 'react';
import Profiles from './profiles';
import Accounts from './accounts';
import Settings from './settings';
import Budget from './budget';
import Calendar from './calendar';

export default function Home() {
  const [profileId, setProfileId] = useState('');
  const [profile, setProfile] = useState(null);
  const [accounts, setAccounts] = useState([]);
  const [budgetItems, setBudgetItems] = useState([]);
  const [budgetGroups, setBudgetGroups] = useState([]);
  const [section, setSection] = useState('calendar');

  useEffect(() => {
    if (profileId) {
        fetch(`http://localhost:8000/profiles/${profileId}`).then(res => res.json()).then(data => {
            console.log(data);
            setProfile(data);
            setAccounts(data.accounts);
            setBudgetItems(data.budget_items);
            setBudgetGroups(data.budget_groups);
        });
    }
  }, [profileId]);

  return (
    <main className="flex flex-col min-h-screen bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100 font-sans">
        <header className="flex items-center justify-between p-2 bg-white dark:bg-gray-800 shadow-md rounded-b-lg">
            <h1 className="text-4xl font-bold mb-1">Budgie</h1>
            <p>A hopeful budgeting helper!</p>
            {profileId && (
            <ul className="flex space-x-2 text-sm font-medium text-center text-gray-500 dark:text-gray-400">
                <li>
                <button
                    onClick={() => setSection('calendar')}
                    className={`inline-block px-4 py-2 rounded-lg transition-colors duration-200 ease-in-out
                    ${section === 'calendar'
                        ? 'text-blue-700 bg-blue-100 dark:bg-blue-900 dark:text-blue-300 shadow-sm'
                        : 'hover:text-gray-700 hover:bg-gray-100 dark:hover:bg-gray-700 dark:hover:text-gray-200'
                    }`}
                    aria-current={section === 'calendar' ? 'page' : undefined}
                >
                    Calendar
                </button>
                </li>
                <li>
                <button
                    onClick={() => setSection('accounts')}
                    className={`inline-block px-4 py-2 rounded-lg transition-colors duration-200 ease-in-out
                    ${section === 'accounts'
                        ? 'text-blue-700 bg-blue-100 dark:bg-blue-900 dark:text-blue-300 shadow-sm'
                        : 'hover:text-gray-700 hover:bg-gray-100 dark:hover:bg-gray-700 dark:hover:text-gray-200'
                    }`}
                >
                    Accounts
                </button>
                </li>
                <li>
                <button
                    onClick={() => setSection('budget')}
                    className={`inline-block px-4 py-2 rounded-lg transition-colors duration-200 ease-in-out
                    ${section === 'budget'
                        ? 'text-blue-700 bg-blue-100 dark:bg-blue-900 dark:text-blue-300 shadow-sm'
                        : 'hover:text-gray-700 hover:bg-gray-100 dark:hover:bg-gray-700 dark:hover:text-gray-200'
                    }`}
                >
                    Budget
                </button>
                </li>
                <li>
                    <button
                        onClick={() => setSection('settings')}
                        className={`inline-block px-4 py-2 rounded-lg transition-colors duration-200 ease-in-out
                        ${section === 'settings'
                            ? 'text-blue-700 bg-blue-100 dark:bg-blue-900 dark:text-blue-300 shadow-sm'
                            : 'hover:text-gray-700 hover:bg-gray-100 dark:hover:bg-gray-700 dark:hover:text-gray-200'
                        }`}
                    >
                        Settings
                    </button>
                </li>
                <li>
                    <button
                        onClick={() => setProfileId('')}
                        className="inline-block px-4 py-2 rounded-lg transition-colors duration-200 ease-in-out hover:text-gray-700 hover:bg-gray-100 dark:hover:bg-gray-700 dark:hover:text-gray-200"
                    >
                        Switch Profile
                    </button>
                </li>
            </ul>
            )}
        </header>
      {profileId && (
        <div className="text-xl text-gray-700 dark:text-gray-300 p-4">
          {section === 'calendar' && <Calendar profileId={profileId} />}
          {section === 'accounts' && <Accounts profileId={profileId} accounts={accounts} />}
          {section === 'budget' && <Budget profileId={profileId} budgetItems={budgetItems} budgetGroups={budgetGroups} />}
          {section === 'settings' && <Settings profileId={profileId} />}
        </div>
      )}
      {!profileId && <Profiles setProfileId={setProfileId} /> }
    </main>
  );
}
