"use client";

import { useSyncExternalStore } from "react";

import type {
  MyHomioActivitySnapshot,
  MyHomioRecentSearch,
  MyHomioRecentView,
  MyHomioSavedSearch,
  MyHomioSearchDraft,
  MyHomioSearchIntent,
} from "./my-homio.types";

const STORAGE_KEY = "homio.my-activity.v1";

const MAX_RECENT_SEARCHES = 12;
const MAX_SAVED_SEARCHES = 12;
const MAX_RECENT_VIEWS = 12;

const SEARCH_INTENTS = [
  "buy",
  "rent",
  "commercial",
  "projects",
  "land",
] as const;

const EMPTY_ACTIVITY: MyHomioActivitySnapshot = {
  recentSearches: [],
  savedSearches: [],
  recentViews: [],
};

let snapshot: MyHomioActivitySnapshot = EMPTY_ACTIVITY;
let initialized = false;

const listeners = new Set<() => void>();

function isRecord(value: unknown): value is Record<string, unknown> {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value)
  );
}

function isText(
  value: unknown,
  maximumLength = 500,
): value is string {
  return (
    typeof value === "string" &&
    value.trim().length > 0 &&
    value.length <= maximumLength
  );
}

function isInternalHref(value: unknown): value is string {
  return (
    typeof value === "string" &&
    value.length <= 4096 &&
    value.startsWith("/") &&
    !value.startsWith("//") &&
    !value.includes("\\") &&
    !/[\u0000-\u001f]/.test(value)
  );
}

function isSearchIntent(
  value: unknown,
): value is MyHomioSearchIntent {
  return (
    typeof value === "string" &&
    (SEARCH_INTENTS as readonly string[]).includes(value)
  );
}

function isTimestamp(value: unknown): value is string {
  return (
    typeof value === "string" &&
    value.length <= 80 &&
    Number.isFinite(Date.parse(value))
  );
}

function isSearchDraft(value: unknown): value is MyHomioSearchDraft {
  if (!isRecord(value)) {
    return false;
  }

  return (
    isInternalHref(value.href) &&
    isSearchIntent(value.intent) &&
    isText(value.title, 240) &&
    (value.location === undefined || isText(value.location, 240)) &&
    (value.filtersLabel === undefined ||
      isText(value.filtersLabel, 240))
  );
}

function isRecentSearch(
  value: unknown,
): value is MyHomioRecentSearch {
  return (
    isRecord(value) &&
    isSearchDraft(value) &&
    isText(value.id, 4096) &&
    isTimestamp(value.searchedAt)
  );
}

function isSavedSearch(
  value: unknown,
): value is MyHomioSavedSearch {
  return (
    isRecord(value) &&
    isSearchDraft(value) &&
    isText(value.id, 4096) &&
    isTimestamp(value.savedAt)
  );
}

function isRecentView(
  value: unknown,
): value is MyHomioRecentView {
  if (!isRecord(value)) {
    return false;
  }

  return (
    isText(value.id, 360) &&
    (value.kind === "property" || value.kind === "project") &&
    isText(value.title, 240) &&
    isInternalHref(value.href) &&
    (value.subtitle === undefined ||
      isText(value.subtitle, 240)) &&
    isTimestamp(value.viewedAt)
  );
}

function restoreSnapshot(value: unknown): MyHomioActivitySnapshot {
  if (!isRecord(value)) {
    return {
      recentSearches: [],
      savedSearches: [],
      recentViews: [],
    };
  }

  const recentSearches = Array.isArray(value.recentSearches)
    ? value.recentSearches
        .filter(isRecentSearch)
        .slice(0, MAX_RECENT_SEARCHES)
    : [];

  const savedSearches = Array.isArray(value.savedSearches)
    ? value.savedSearches
        .filter(isSavedSearch)
        .slice(0, MAX_SAVED_SEARCHES)
    : [];

  const recentViews = Array.isArray(value.recentViews)
    ? value.recentViews
        .filter(isRecentView)
        .slice(0, MAX_RECENT_VIEWS)
    : [];

  return {
    recentSearches,
    savedSearches,
    recentViews,
  };
}

/**
 * Restore activity from the current browser tab.
 * Server rendering always starts from the empty snapshot.
 */
function ensureBrowserSession(): void {
  if (initialized) {
    return;
  }

  initialized = true;

  if (typeof window === "undefined") {
    return;
  }

  try {
    const storedValue = window.sessionStorage.getItem(STORAGE_KEY);

    if (!storedValue) {
      snapshot = {
        recentSearches: [],
        savedSearches: [],
        recentViews: [],
      };
      return;
    }

    snapshot = restoreSnapshot(JSON.parse(storedValue));
  } catch {
    // Invalid, unavailable or blocked browser storage must not break My HOMIO.
    snapshot = {
      recentSearches: [],
      savedSearches: [],
      recentViews: [],
    };
  }
}

function persistSnapshot(): void {
  if (typeof window === "undefined") {
    return;
  }

  try {
    window.sessionStorage.setItem(
      STORAGE_KEY,
      JSON.stringify(snapshot),
    );
  } catch {
    // Continue with in-memory activity if browser storage is unavailable.
  }
}

function publish(next: MyHomioActivitySnapshot): void {
  ensureBrowserSession();

  snapshot = next;
  persistSnapshot();

  for (const listener of listeners) {
    listener();
  }
}

function subscribe(listener: () => void): () => void {
  ensureBrowserSession();
  listeners.add(listener);

  return () => {
    listeners.delete(listener);
  };
}

function getSnapshot(): MyHomioActivitySnapshot {
  ensureBrowserSession();
  return snapshot;
}

function getServerSnapshot(): MyHomioActivitySnapshot {
  return EMPTY_ACTIVITY;
}

/**
 * Browser-tab activity only.
 * This is not account persistence or server-synchronized activity.
 */
export function useMyHomioActivity(): MyHomioActivitySnapshot {
  return useSyncExternalStore(
    subscribe,
    getSnapshot,
    getServerSnapshot,
  );
}

export function recordRecentSearch(
  draft: MyHomioSearchDraft,
): void {
  ensureBrowserSession();

  if (!isSearchDraft(draft)) {
    return;
  }

  // A rerender or pagination change must not keep refreshing the same entry.
  if (snapshot.recentSearches[0]?.href === draft.href) {
    return;
  }

  const entry: MyHomioRecentSearch = {
    ...draft,
    id: draft.href,
    searchedAt: new Date().toISOString(),
  };

  publish({
    ...snapshot,
    recentSearches: [
      entry,
      ...snapshot.recentSearches.filter(
        (item) => item.href !== draft.href,
      ),
    ].slice(0, MAX_RECENT_SEARCHES),
  });
}

export function toggleSavedSearch(
  draft: MyHomioSearchDraft,
): void {
  ensureBrowserSession();

  if (!isSearchDraft(draft)) {
    return;
  }

  const existing = snapshot.savedSearches.some(
    (item) => item.href === draft.href,
  );

  if (existing) {
    publish({
      ...snapshot,
      savedSearches: snapshot.savedSearches.filter(
        (item) => item.href !== draft.href,
      ),
    });

    return;
  }

  const entry: MyHomioSavedSearch = {
    ...draft,
    id: draft.href,
    savedAt: new Date().toISOString(),
  };

  publish({
    ...snapshot,
    savedSearches: [
      entry,
      ...snapshot.savedSearches.filter(
        (item) => item.href !== draft.href,
      ),
    ].slice(0, MAX_SAVED_SEARCHES),
  });
}

export function removeRecentSearch(id: string): void {
  ensureBrowserSession();

  publish({
    ...snapshot,
    recentSearches: snapshot.recentSearches.filter(
      (item) => item.id !== id,
    ),
  });
}

export function clearRecentSearches(): void {
  ensureBrowserSession();

  publish({
    ...snapshot,
    recentSearches: [],
  });
}

export function removeSavedSearch(id: string): void {
  ensureBrowserSession();

  publish({
    ...snapshot,
    savedSearches: snapshot.savedSearches.filter(
      (item) => item.id !== id,
    ),
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
  ensureBrowserSession();

  if (
    !isText(view.id, 180) ||
    !isText(view.title, 240) ||
    !isInternalHref(view.href) ||
    (view.kind !== "property" && view.kind !== "project") ||
    (view.subtitle !== undefined && !isText(view.subtitle, 240))
  ) {
    return;
  }

  // Property and project records may share a raw ID; keep their identities separate.
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
        (item) => item.id !== identity,
      ),
    ].slice(0, MAX_RECENT_VIEWS),
  });
}

export function removeRecentView(id: string): void {
  ensureBrowserSession();

  publish({
    ...snapshot,
    recentViews: snapshot.recentViews.filter(
      (item) => item.id !== id,
    ),
  });
}

export function clearRecentViews(): void {
  ensureBrowserSession();

  publish({
    ...snapshot,
    recentViews: [],
  });
}

export function clearAllActivity(): void {
  publish({
    recentSearches: [],
    savedSearches: [],
    recentViews: [],
  });
}
