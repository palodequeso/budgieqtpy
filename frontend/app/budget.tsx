// frontend/app/page.tsx
"use client";

export default function Budget({ profileId, budgetItems, budgetGroups }: { profileId: string, budgetItems: any[], budgetGroups: any[] }) {
    return (
        <main className="flex flex-col items-center justify-center p-24">
            <h1 className="text-4xl font-bold mb-8">Budget</h1>
                {budgetItems.length === 0 ? (
                    <p>No profiles found.</p>
                ) : (
                    <div className="max-h-96 overflow-y-auto">
                        {budgetItems.map((item: any) => (
                            <button
                                key={item.id}
                                className="ml-4 px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                            >
                                {item.name}
                            </button>
                        ))}
                    </div>
                )}
        </main>
    );
}
