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
    params.set("country", "India");
    params.set("city", "Pune");

    const normalizedQuery = query.trim();

    if (normalizedQuery) {
      params.set("q", normalizedQuery);
    }

    router.push(`/search?${params.toString()}`);
  }

  return (
    <form
      className={styles.search}
      onSubmit={handleSubmit}
    >
      <div className={styles.location}>
        <span className={styles.icon} aria-hidden="true">
          ◎
        </span>

        <div className={styles.field}>
          <label htmlFor="homio-search">
            Pune locality, project or landmark
          </label>

          <input
            id="homio-search"
            name="q"
            type="text"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Try Baner, Wakad, Kharadi..."
            autoComplete="off"
            maxLength={120}
          />
        </div>
      </div>

      <button
        type="submit"
        className={styles.searchButton}
      >
        Search
      </button>
    </form>
  );
}
