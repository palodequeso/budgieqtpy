// frontend/app/page.tsx
"use client";

import { useState, useEffect } from 'react';

export default function Settings({ profileId }: { profileId: string }) {
    return (
        <main className="flex flex-col items-center justify-center p-24">
            <h1 className="text-4xl font-bold mb-8">Settings: {profileId}</h1>
        </main>
    );
}
