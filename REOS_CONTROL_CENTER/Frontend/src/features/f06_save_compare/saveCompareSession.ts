"use client";

import { useSyncExternalStore } from "react";

import type { CompareItem } from "./compare.types";
import type { SavedRecord } from "./saved.types";

type SaveCompareSession = Readonly<{
  savedRecords: readonly SavedRecord[];
  comparedItems: readonly CompareItem[];
}>;

const EMPTY_SESSION: SaveCompareSession = {
  savedRecords: [],
  comparedItems: [],
};

let snapshot: SaveCompareSession = EMPTY_SESSION;
const listeners = new Set<() => void>();

function publish(next: SaveCompareSession): void {
  snapshot = next;
  listeners.forEach((listener) => listener());
}

function subscribe(listener: () => void) {
  listeners.add(listener);

  return () => {
    listeners.delete(listener);
  };
}

function getSnapshot(): SaveCompareSession {
  return snapshot;
}

function getServerSnapshot(): SaveCompareSession {
  return EMPTY_SESSION;
}

/**
 * Shared in-memory state for the current browser application session.
 * No localStorage, cookie storage, or account-sync claims.
 * A full page reload clears this state until an approved persistence
 * service is connected.
 */
export function useSaveCompareSession() {
  return useSyncExternalStore(
    subscribe,
    getSnapshot,
    getServerSnapshot,
  );
}

export function toggleSavedRecord(record: SavedRecord): void {
  const exists = snapshot.savedRecords.some(
    (item) => item.id === record.id && item.kind === record.kind,
  );

  publish({
    ...snapshot,
    savedRecords: exists
      ? snapshot.savedRecords.filter(
          (item) => item.id !== record.id || item.kind !== record.kind,
        )
      : [...snapshot.savedRecords, record],
  });
}

export function removeSavedRecord(id: string): void {
  publish({
    ...snapshot,
    savedRecords: snapshot.savedRecords.filter(
      (item) => item.id !== id,
    ),
  });
}

export function toggleComparedItem(item: CompareItem): void {
  const exists = snapshot.comparedItems.some(
    (current) => current.id === item.id && current.kind === item.kind,
  );

  if (exists) {
    publish({
      ...snapshot,
      comparedItems: snapshot.comparedItems.filter(
        (current) => current.id !== item.id || current.kind !== item.kind,
      ),
    });
    return;
  }

  if (snapshot.comparedItems.length >= 4) {
    return;
  }

  publish({
    ...snapshot,
    comparedItems: [...snapshot.comparedItems, item],
  });
}

export function removeComparedItem(id: string): void {
  publish({
    ...snapshot,
    comparedItems: snapshot.comparedItems.filter(
      (item) => item.id !== id,
    ),
  });
}

export function clearComparedItems(): void {
  publish({
    ...snapshot,
    comparedItems: [],
  });
}
