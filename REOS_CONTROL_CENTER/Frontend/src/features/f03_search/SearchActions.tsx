"use client";

import { useState } from "react";

import type { SearchState } from "./search.types";
import {
  countActiveFilters,
  resetSearchState,
  searchStateToParams,
} from "./search.utils";
import styles from "./SearchActions.module.css";

type SearchActionsProps = Readonly<{
  state: SearchState;
  onChange: (state: SearchState) => void;
}>;

export default function SearchActions({
  state,
  onChange,
}: SearchActionsProps) {
  const [shareStatus, setShareStatus] = useState("");

  async function handleShare() {
    if (typeof window === "undefined") {
      return;
    }

    const params = searchStateToParams(state);
    const search = params.toString();
    const url = new URL(window.location.href);

    url.search = search;

    const shareUrl = url.toString();

    setShareStatus("");

    try {
      if (typeof navigator.share === "function") {
        await navigator.share({
          title: "HOMIO Property Search",
          text: "Explore this HOMIO search preview.",
          url: shareUrl,
        });

        return;
      }

      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(shareUrl);
        setShareStatus("Search link copied.");
        return;
      }

      setShareStatus(
        "Sharing is unavailable in this browser. Copy the page URL manually.",
      );
    } catch (error) {
      if (
        error instanceof DOMException &&
        error.name === "AbortError"
      ) {
        return;
      }

      setShareStatus(
        "The search link could not be shared automatically. Copy the page URL manually.",
      );
    }
  }

  const hasFilters = countActiveFilters(state.filters) > 0;

  return (
    <div>
      <div className={styles.actions}>
        <button
          type="button"
          className={styles.secondary}
          disabled={!hasFilters}
          onClick={() => onChange(resetSearchState(state))}
          style={
            !hasFilters
              ? { opacity: 0.55, cursor: "not-allowed" }
              : undefined
          }
        >
          Clear filters
        </button>

        <button
          type="button"
          className={styles.secondary}
          onClick={handleShare}
        >
          Share search
        </button>

        <button
          type="button"
          className={styles.primary}
          disabled
          title="Saved-search persistence is not connected to My HOMIO yet."
          aria-describedby="search-save-unavailable"
          style={{ opacity: 0.55, cursor: "not-allowed" }}
        >
          Save search
        </button>
      </div>

      <p
        id="search-save-unavailable"
        style={{
          margin: "8px 0 0",
          color: "#667085",
          fontSize: 11,
        }}
      >
        Save search is disabled until account-backed My HOMIO persistence
        is connected. No saved search will be created by this preview.
      </p>

      <p
        aria-live="polite"
        style={{
          margin: shareStatus ? "8px 0 0" : 0,
          color: "#34414d",
          fontSize: 11,
        }}
      >
        {shareStatus}
      </p>
    </div>
  );
}
