import { useStore } from '../store/store';

function getBaseUrl(): string {
  const url = useStore.getState().serverUrl;
  if (!url) throw new Error('Server URL not configured');
  return url.replace(/\/$/, ''); // strip trailing slash
}

export const api = {
  async get<T>(path: string): Promise<T> {
    const res = await fetch(`${getBaseUrl()}${path}`, {
      headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) throw new Error(`API ${path}: ${res.status}`);
    return res.json();
  },

  async post<T>(path: string, body: unknown): Promise<T> {
    const res = await fetch(`${getBaseUrl()}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`API ${path}: ${res.status}`);
    return res.json();
  },

  async put<T>(path: string, body: unknown): Promise<T> {
    const res = await fetch(`${getBaseUrl()}${path}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`API ${path}: ${res.status}`);
    return res.json();
  },

  async del<T>(path: string): Promise<T> {
    const res = await fetch(`${getBaseUrl()}${path}`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) throw new Error(`API ${path}: ${res.status}`);
    return res.json();
  },
};
