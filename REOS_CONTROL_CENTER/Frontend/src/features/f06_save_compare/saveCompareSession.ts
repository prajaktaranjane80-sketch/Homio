"use client";

import { useSyncExternalStore } from "react";

import type {
  CompareEntityKind,
  CompareItem,
} from "./compare.types";

import type {
  SavedEntityKind,
  SavedRecord,
} from "./saved.types";

export type SaveCompareSession = Readonly<{
  savedRecords: readonly SavedRecord[];
  comparedItems: readonly CompareItem[];
}>;

const EMPTY_SESSION: SaveCompareSession = {
  savedRecords: [],
  comparedItems: [],
};

const MAX_COMPARE_ITEMS = 4;

let snapshot: SaveCompareSession = EMPTY_SESSION;

const listeners = new Set<() => void>();

function publish(next: SaveCompareSession): void {
  if (
    next.savedRecords === snapshot.savedRecords &&
    next.comparedItems === snapshot.comparedItems
  ) {
    return;
  }

  snapshot = next;

  for (const listener of listeners) {
    listener();
  }
}

function subscribe(listener: () => void): () => void {
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
 * Browser-session state only.
 *
 * This store does not persist data to an account, localStorage,
 * cookies, or a backend. A full page reload resets its contents.
 */
export function useSaveCompareSession(): SaveCompareSession {
  return useSyncExternalStore(
    subscribe,
    getSnapshot,
    getServerSnapshot,
  );
}

export function toggleSavedRecord(record: SavedRecord): void {
  const exists = snapshot.savedRecords.some(
    (item) =>
      item.id === record.id &&
      item.kind === record.kind,
  );

  const savedRecords = exists
    ? snapshot.savedRecords.filter(
        (item) =>
          item.id !== record.id ||
          item.kind !== record.kind,
      )
    : [...snapshot.savedRecords, record];

  publish({
    ...snapshot,
    savedRecords,
  });
}

export function removeSavedRecord(
  id: string,
  kind?: SavedEntityKind,
): void {
  const savedRecords = snapshot.savedRecords.filter(
    (item) =>
      item.id !== id ||
      (kind !== undefined && item.kind !== kind),
  );

  publish({
    ...snapshot,
    savedRecords,
  });
}

export function toggleComparedItem(item: CompareItem): boolean {
  const exists = snapshot.comparedItems.some(
    (current) =>
      current.id === item.id &&
      current.kind === item.kind,
  );

  if (exists) {
    removeComparedItem(item.id, item.kind);
    return false;
  }

  if (snapshot.comparedItems.length >= MAX_COMPARE_ITEMS) {
    return false;
  }

  publish({
    ...snapshot,
    comparedItems: [
      ...snapshot.comparedItems,
      item,
    ],
  });

  return true;
}

export function removeComparedItem(
  id: string,
  kind?: CompareEntityKind,
): void {
  const comparedItems = snapshot.comparedItems.filter(
    (item) =>
      item.id !== id ||
      (kind !== undefined && item.kind !== kind),
  );

  publish({
    ...snapshot,
    comparedItems,
  });
}

export function clearComparedItems(): void {
  publish({
    ...snapshot,
    comparedItems: [],
  });
}
