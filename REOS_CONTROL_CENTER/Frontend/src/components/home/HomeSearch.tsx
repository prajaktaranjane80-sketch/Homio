"use client";

import { FormEvent, useState } from "react";
import styles from "./HomeSearch.module.css";

export default function HomeSearch() {
  const [query, setQuery] = useState("");

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
  }

  return (
    <form className={styles.search} onSubmit={handleSubmit}>
      <div className={styles.location}>
        <span className={styles.icon} aria-hidden="true">
          ◎
        </span>

        <div className={styles.field}>
          <label htmlFor="homio-search">Location, project or landmark</label>
          <input
            id="homio-search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Dubai, Singapore, Tokyo..."
            autoComplete="off"
          />
        </div>
      </div>

      <button type="button" className={styles.filterButton}>
        <span>Filters</span>
        <span aria-hidden="true">⌄</span>
      </button>

      <button type="submit" className={styles.searchButton}>
        Search
      </button>
    </form>
  );
}
