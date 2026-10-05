"use client";

import type { SearchState } from "./search.types";
import { resetSearchState } from "./search.utils";
import styles from "./SearchActions.module.css";

type SearchActionsProps = Readonly<{
  state: SearchState;
  onChange: (state: SearchState) => void;
}>;

export default function SearchActions({
  state,
  onChange,
}: SearchActionsProps) {
  async function handleShare() {
    const url =
      typeof window !== "undefined"
        ? window.location.href
        : "";

    if (!url) {
      return;
    }

    if (navigator.share) {
      await navigator.share({
        title: "HOMIO Property Search",
        text: "Explore this HOMIO property search.",
        url,
      });
      return;
    }

    await navigator.clipboard?.writeText(url);
  }

  return (
    <div className={styles.actions}>
      <button
        type="button"
        className={styles.secondary}
        onClick={() => onChange(resetSearchState(state))}
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
        onClick={() => {
          // Saved-search persistence is intentionally deferred to the F07
          // My HOMIO integration boundary.
        }}
      >
        Save search
      </button>
    </div>
  );
}
