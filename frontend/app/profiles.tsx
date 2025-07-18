// frontend/app/page.tsx
"use client";

import { useState, useEffect } from 'react';

export default function Profiles() {
    const [profiles, setProfiles] = useState([]);

    useEffect(() => {
        fetch('http://localhost:8000/profiles').then(res => res.json()).then(data => {
            console.log(data);
            setProfiles(data);
        }).catch(err => console.error(err));
    }, []);
    return (
        <main className="flex flex-col items-center justify-center p-24">
            <h1 className="text-4xl font-bold mb-8">Profiles</h1>
                {profiles.length === 0 ? (
                    <p>No profiles found.</p>
                ) : (
                    <div className="max-h-96 overflow-y-auto">
                        {profiles.map((profile: any) => (
                            <button
                                key={profile.id}
                                className="ml-4 px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                            >
                                {profile.name}
                            </button>
                        ))}
                    </div>
                )}
        </main>
    );
}
