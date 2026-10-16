"use client";

import { useRouter } from "next/navigation";
import { useId, useState } from "react";

import SearchAutocomplete from "./SearchAutocomplete";
import styles from "./SearchExperience.module.css";
import type { SearchSuggestion } from "./SearchExperience.types";

type Props = Readonly<{
  suggestions?: readonly SearchSuggestion[];
  recent?: readonly SearchSuggestion[];
  popular?: readonly SearchSuggestion[];
}>;

export default function SearchOverlay({
  suggestions = [],
  recent = [],
  popular = [],
}: Props) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const panelId = useId();

  function submitSearch() {
    const normalized = query.trim();
    if (!normalized) return;

    setOpen(false);
    router.push(`/search?q=${encodeURIComponent(normalized)}`);
  }

  return (
    <div className={styles.searchOverlayRoot}>
      <button
        type="button"
        className={styles.searchOverlayTrigger}
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen(true)}
      >
        <span aria-hidden="true">⌕</span>
        Search HOMIO
      </button>

      {open ? (
        <div
          className={styles.searchOverlayBackdrop}
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) setOpen(false);
          }}
        >
          <section
            className={styles.searchOverlayPanel}
            id={panelId}
            aria-label="Global property search"
            role="dialog"
            aria-modal="true"
          >
            <header className={styles.searchOverlayHeader}>
              <div>
                <span className={styles.searchOverline}>HOMIO DISCOVERY</span>
                <h2 className={styles.searchOverlayTitle}>Where would you like to look?</h2>
              </div>

              <button
                className={styles.searchClose}
                type="button"
                aria-label="Close search"
                onClick={() => setOpen(false)}
              >
                ×
              </button>
            </header>

            <form
              onSubmit={(event) => {
                event.preventDefault();
                submitSearch();
              }}
            >
              <SearchAutocomplete
                query={query}
                onQueryChange={setQuery}
                suggestions={suggestions}
                recent={recent}
                popular={popular}
              />
              <p className={styles.searchHint}>
                Search results depend on configured sources. Suggestions are
                shown only when supplied by the calling experience.
              </p>
            </form>
          </section>
        </div>
      ) : null}
    </div>
  );
}
