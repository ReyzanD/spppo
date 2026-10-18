import { useCallback, useEffect, useState } from 'react';

const STORAGE_KEY = 'pesan-aman.history.v1';
const MAX_ITEMS = 100;

function isValidEntry(entry) {
  return (
    entry &&
    typeof entry === 'object' &&
    typeof entry.id === 'string' &&
    typeof entry.message === 'string' &&
    typeof entry.label === 'string' &&
    entry.probabilities &&
    typeof entry.probabilities === 'object'
  );
}

function readHistory() {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.filter(isValidEntry) : [];
  } catch {
    return [];
  }
}

function createId() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function useHistory() {
  const [items, setItems] = useState(readHistory);

  useEffect(() => {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
    } catch {
      // Storage can be unavailable in private mode; history still works in memory.
    }
  }, [items]);

  const add = useCallback((entry) => {
    setItems((current) => {
      const next = [{ ...entry, id: entry.id || createId() }, ...current];
      return next.slice(0, MAX_ITEMS);
    });
  }, []);

  const remove = useCallback((id) => {
    setItems((current) => current.filter((item) => item.id !== id));
  }, []);

  const clear = useCallback(() => setItems([]), []);

  return { items, add, remove, clear };
}
