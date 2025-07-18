// frontend/app/page.tsx
"use client";

import { useState, useEffect } from 'react';
import Profiles from './profiles';

export default function Home() {
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [itemId, setItemId] = useState('');
  const [itemResponse, setItemResponse] = useState('');

  const fetchItem = async () => {
    if (!itemId) {
      setItemResponse("Please enter an item ID.");
      return;
    }
    try {
      const response = await fetch(`http://localhost:8000/profile/${itemId}?q=test`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setItemResponse(JSON.stringify(data, null, 2));
    } catch (e: any) { // Use 'any' for error type if you're not strictly typing it
      console.error("Error fetching item:", e);
      setItemResponse(`Failed to fetch item: ${e.message}`);
    }
  };

  return (
    <main className="flex flex-col items-center justify-center p-24">
      <h1 className="text-4xl font-bold mb-8">Budgie</h1>
      <Profiles />
      {/* {error && <p className="text-red-500 mb-4">{error}</p>}
      <div className="w-full mb-8 p-6 border rounded-lg shadow-lg bg-gray-10">
        <h2 className="text-2xl font-semibold mb-4">Fetch Item by ID:</h2>
        <input
          type="number"
          value={itemId}
          onChange={(e) => setItemId(e.target.value)}
          placeholder="Enter Item ID"
          className="px-4 py-2 border rounded-md mb-4 w-64"
        />
        <button
          onClick={fetchItem}
          className="ml-4 px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          Fetch Item
        </button>
        {itemResponse && (
          <pre style={{
            overflowY: 'scroll',
            overflowX: 'auto',
            maxHeight: 'calc(100vh - 500px)',
          }} className="mt-4 p-4 bg-gray-20 rounded-md text-sm whitespace-pre-wrap">
            {itemResponse}
          </pre>
        )}
      </div> */}
    </main>
  );
}
