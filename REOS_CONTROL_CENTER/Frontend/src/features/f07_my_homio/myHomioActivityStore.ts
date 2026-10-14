"use client";

import { useEffect, useSyncExternalStore } from "react";

import type {
  MyHomioActivitySnapshot,
  MyHomioRecentSearch,
  MyHomioRecentView,
  MyHomioSavedSearch,
  MyHomioSearchDraft,
} from "./my-homio.types";

const STORAGE_KEY = "homio:f07:activity:v1";
const MAX_RECENT_SEARCHES = 12;
const MAX_SAVED_SEARCHES = 12;
const MAX_RECENT_VIEWS = 12;

const EMPTY_ACTIVITY: MyHomioActivitySnapshot = {
  recentSearches: [],
  savedSearches: [],
  recentViews: [],
};

let snapshot: MyHomioActivitySnapshot = EMPTY_ACTIVITY;
let hydrated = false;

const listeners = new Set<() => void>();

function notify(): void {
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

function getSnapshot(): MyHomioActivitySnapshot {
  return snapshot;
}

function getServerSnapshot(): MyHomioActivitySnapshot {
  return EMPTY_ACTIVITY;
}

function isObject(value: unknown): value is Record<string, unknown> {
  return Boolean(
    value &&
      typeof value === "object" &&
      !Array.isArray(value),
  );
}

function isText(value: unknown, maxLength = 500): value is string {
  return (
    typeof value === "string" &&
    value.length > 0 &&
    value.length <= maxLength
  );
}

function isInternalHref(value: unknown): value is string {
  return (
    typeof value === "string" &&
    value.length <= 2048 &&
    value.startsWith("/") &&
    !value.startsWith("//") &&
    !/[\\\u0000-\u001F]/.test(value)
  );
}

function isIntent(
  value: unknown,
): value is MyHomioSearchDraft["intent"] {
  return (
    value === "buy" ||
    value === "rent" ||
    value === "commercial" ||
    value === "projects" ||
    value === "land"
  );
}

function isTimestamp(value: unknown): value is string {
  return (
    typeof value === "string" &&
    value.length <= 40 &&
    Number.isFinite(Date.parse(value))
  );
}

function hash(value: string): string {
  let result = 2166136261;

  for (let index = 0; index < value.length; index += 1) {
    result ^= value.charCodeAt(index);
    result = Math.imul(result, 16777619);
  }

  return (result >>> 0).toString(16).padStart(8, "0");
}

function isSearchDraft(value: unknown): value is MyHomioSearchDraft {
  if (!isObject(value)) {
    return false;
  }

  return (
    isInternalHref(value.href) &&
    isIntent(value.intent) &&
    isText(value.title, 240) &&
    (value.location === undefined ||
      typeof value.location === "string") &&
    (value.filtersLabel === undefined ||
      typeof value.filtersLabel === "string")
  );
}

function isRecentSearch(value: unknown): value is MyHomioRecentSearch {
  return (
    isSearchDraft(value) &&
    isText((value as Record<string, unknown>).id, 100) &&
    isTimestamp((value as Record<string, unknown>).searchedAt)
  );
}

function isSavedSearch(value: unknown): value is MyHomioSavedSearch {
  return (
    isSearchDraft(value) &&
    isText((value as Record<string, unknown>).id, 100) &&
    isTimestamp((value as Record<string, unknown>).savedAt)
  );
}

function isRecentView(value: unknown): value is MyHomioRecentView {
  if (!isObject(value)) {
    return false;
  }

  return (
    isText(value.id, 240) &&
    (value.kind === "property" || value.kind === "project") &&
    isText(value.title, 240) &&
    isInternalHref(value.href) &&
    (value.subtitle === undefined ||
      typeof value.subtitle === "string") &&
    isTimestamp(value.viewedAt)
  );
}

function sanitizeSnapshot(value: unknown): MyHomioActivitySnapshot {
  if (!isObject(value)) {
    return EMPTY_ACTIVITY;
  }

  const recentSearches = Array.isArray(value.recentSearches)
    ? value.recentSearches.filter(isRecentSearch).slice(0, MAX_RECENT_SEARCHES)
    : [];

  const savedSearches = Array.isArray(value.savedSearches)
    ? value.savedSearches.filter(isSavedSearch).slice(0, MAX_SAVED_SEARCHES)
    : [];

  const recentViews = Array.isArray(value.recentViews)
    ? value.recentViews.filter(isRecentView).slice(0, MAX_RECENT_VIEWS)
    : [];

  return {
    recentSearches,
    savedSearches,
    recentViews,
  };
}

function hydrateFromSessionStorage(): void {
  if (typeof window === "undefined" || hydrated) {
    return;
  }

  hydrated = true;

  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY);

    if (raw) {
      snapshot = sanitizeSnapshot(JSON.parse(raw) as unknown);
    }
  } catch {
    snapshot = EMPTY_ACTIVITY;
  }

  notify();
}

function publish(next: MyHomioActivitySnapshot): void {
  snapshot = next;

  if (typeof window !== "undefined") {
    try {
      window.sessionStorage.setItem(
        STORAGE_KEY,
        JSON.stringify(snapshot),
      );
    } catch {
      // Storage can be blocked or full. The in-memory session still works.
    }
  }

  notify();
}

function ensureBrowserSession(): boolean {
  if (typeof window === "undefined") {
    return false;
  }

  hydrateFromSessionStorage();
  return true;
}

export function useMyHomioActivity(): MyHomioActivitySnapshot {
  const activity = useSyncExternalStore(
    subscribe,
    getSnapshot,
    getServerSnapshot,
  );

  useEffect(() => {
    hydrateFromSessionStorage();
  }, []);

  return activity;
}

export function recordRecentSearch(draft: MyHomioSearchDraft): void {
  if (!ensureBrowserSession() || !isSearchDraft(draft)) {
    return;
  }

  const record: MyHomioRecentSearch = {
    ...draft,
    id: `recent-search-${hash(draft.href)}`,
    searchedAt: new Date().toISOString(),
  };

  publish({
    ...snapshot,
    recentSearches: [
      record,
      ...snapshot.recentSearches.filter(
        (item) => item.href !== record.href,
      ),
    ].slice(0, MAX_RECENT_SEARCHES),
  });
}

/**
 * Returns true if the requirement is saved after this operation,
 * or false if an existing saved requirement was removed.
 *
 * This is a browser-session saved search, not an alert subscription.
 */
export function toggleSavedSearch(draft: MyHomioSearchDraft): boolean {
  if (!ensureBrowserSession() || !isSearchDraft(draft)) {
    return false;
  }

  const existing = snapshot.savedSearches.find(
    (item) => item.href === draft.href,
  );

  if (existing) {
    publish({
      ...snapshot,
      savedSearches: snapshot.savedSearches.filter(
        (item) => item.href !== draft.href,
      ),
    });

    return false;
  }

  const saved: MyHomioSavedSearch = {
    ...draft,
    id: `saved-search-${hash(draft.href)}`,
    savedAt: new Date().toISOString(),
  };

  publish({
    ...snapshot,
    savedSearches: [
      saved,
      ...snapshot.savedSearches,
    ].slice(0, MAX_SAVED_SEARCHES),
  });

  return true;
}

export function removeSavedSearch(id: string): void {
  if (!ensureBrowserSession()) {
    return;
  }

  publish({
    ...snapshot,
    savedSearches: snapshot.savedSearches.filter(
      (item) => item.id !== id,
    ),
  });
}

export function removeRecentSearch(id: string): void {
  if (!ensureBrowserSession()) {
    return;
  }

  publish({
    ...snapshot,
    recentSearches: snapshot.recentSearches.filter(
      (item) => item.id !== id,
    ),
  });
}

export function clearRecentSearches(): void {
  if (!ensureBrowserSession()) {
    return;
  }

  publish({
    ...snapshot,
    recentSearches: [],
  });
}

export function recordRecentView(
  view: Readonly<{
    id: string;
    kind: "property" | "project";
    title: string;
    href: string;
    subtitle?: string;
  }>,
): void {
  if (
    !ensureBrowserSession() ||
    !isText(view.id, 180) ||
    !isText(view.title, 240) ||
    !isInternalHref(view.href) ||
    (view.kind !== "property" && view.kind !== "project")
  ) {
    return;
  }

  const identity = `${view.kind}:${view.id}`;

  const record: MyHomioRecentView = {
    ...view,
    id: identity,
    viewedAt: new Date().toISOString(),
  };

  publish({
    ...snapshot,
    recentViews: [
      record,
      ...snapshot.recentViews.filter(
        (item) => `${item.kind}:${item.id}` !== identity,
      ),
    ].slice(0, MAX_RECENT_VIEWS),
  });
}

export function removeRecentView(id: string): void {
  if (!ensureBrowserSession()) {
    return;
  }

  publish({
    ...snapshot,
    recentViews: snapshot.recentViews.filter(
      (item) => item.id !== id,
    ),
  });
}

export function clearRecentViews(): void {
  if (!ensureBrowserSession()) {
    return;
  }

  publish({
    ...snapshot,
    recentViews: [],
  });
}

export function clearAllActivity(): void {
  if (!ensureBrowserSession()) {
    return;
  }

  publish(EMPTY_ACTIVITY);
}
