"use client";

import { FormEvent, useMemo, useState } from "react";
import SearchHeader from "./SearchHeader";
import SearchIntentTabs from "./SearchIntentTabs";
import SearchLocationField from "./SearchLocationField";
import type { SearchIntent } from "./search.types";
import styles from "./SearchShell.module.css";

const intents: SearchIntent[] = [
  "buy",
  "rent",
  "commercial",
  "projects",
  "land",
];

export default function SearchShell() {
  const [intent, setIntent] = useState<SearchIntent>("buy");
  const [location, setLocation] = useState("");

  const intentLabel = useMemo(() => {
    return intents
      .find((item) => item === intent)
      ?.replace(/^\w/, (letter) => letter.toUpperCase()) ?? "Buy";
  }, [intent]);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    // Search execution will be connected to the F03 search contract later.
    // This foundation deliberately does not call backend APIs.
  }

  return (
    <section className={styles.shell} aria-labelledby="search-title">
      <div className="homio-container">
        <SearchHeader
          title="Find the right property."
          description="Search homes, projects, commercial spaces and land through one HOMIO experience."
        />

        <form className={styles.searchPanel} onSubmit={handleSubmit}>
          <SearchIntentTabs
            intents={intents}
            activeIntent={intent}
            onChange={setIntent}
          />

          <div className={styles.searchRow}>
            <SearchLocationField
              value={location}
              onChange={setLocation}
              intentLabel={intentLabel}
            />

            <button type="submit" className={styles.submitButton}>
              Search
            </button>
          </div>

          <div className={styles.contextRow} aria-label="Search context">
            <span>{intentLabel}</span>

            <span className={styles.contextSeparator} aria-hidden="true">
              •
            </span>

            <span>
              {location.trim()
                ? location.trim()
                : "Choose a city, locality, project or landmark"}
            </span>
          </div>
        </form>
      </div>
    </section>
  );
}
