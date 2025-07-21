// frontend/app/page.tsx
"use client";

export default function Accounts({ accounts, profileId }: { profileId: string, accounts: any[] }) {
    return (
        <main className="flex flex-col items-center justify-center p-24">
            <h1 className="text-4xl font-bold mb-8">Accounts</h1>
                {accounts.length === 0 ? (
                    <p>No profiles found.</p>
                ) : (
                    <div className="max-h-96 overflow-y-auto">
                        {accounts.map((account: any) => (
                            <button
                                key={account.id}
                                className="ml-4 px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                            >
                                {account.name}
                            </button>
                        ))}
                    </div>
                )}
        </main>
    );
}
