"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import type { FormEvent } from "react";

import type { HomeIntent } from "./HomeHero";
import styles from "./HomeSearch.module.css";

type HomeSearchProps = Readonly<{
  intent: HomeIntent;
}>;

export default function HomeSearch({ intent }: HomeSearchProps) {
  const router = useRouter();
  const [query, setQuery] = useState("");

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const params = new URLSearchParams();
    params.set("intent", intent);

    const normalizedQuery = query.trim();

    if (normalizedQuery) {
      params.set("q", normalizedQuery);
    }

    router.push(`/search?${params.toString()}`);
  }

  return (
    <form className={styles.search} onSubmit={handleSubmit}>
      <div className={styles.location}>
        <span className={styles.icon} aria-hidden="true">
          ◎
        </span>

        <div className={styles.field}>
          <label htmlFor="homio-search">
            City, locality, project or landmark
          </label>

          <input
            id="homio-search"
            name="q"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Dubai, Singapore, Tokyo..."
            autoComplete="off"
          />
        </div>
      </div>

      <button type="submit" className={styles.searchButton}>
        Search
      </button>
    </form>
  );
}
