"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";

import styles from "./AIWorkspace.module.css";

export default function AILocalityComparison() {
  const [first, setFirst] = useState("");
  const [second, setSecond] = useState("");
  const [ready, setReady] = useState(false);
  const [error, setError] = useState("");

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const firstValue = first.trim();
    const secondValue = second.trim();

    if (!firstValue || !secondValue) {
      setError("Enter both localities to prepare a comparison checklist.");
      setReady(false);
      return;
    }

    if (firstValue.toLocaleLowerCase() === secondValue.toLocaleLowerCase()) {
      setError("Enter two different localities.");
      setReady(false);
      return;
    }

    setError("");
    setReady(true);
  }

  function searchHref(location: string): string {
    const params = new URLSearchParams({
      intent: "buy",
      city: location.trim(),
    });

    return `/search?${params.toString()}`;
  }

  return (
    <section
      className={styles.card}
      aria-labelledby="ai-locality-compare-title"
    >
      <div className={styles.cardHeader}>
        <div>
          <p className={styles.kicker}>Compare the context</p>
          <h2 className={styles.cardTitle} id="ai-locality-compare-title">
            Two localities, one checklist
          </h2>
          <p className={styles.muted}>
            Prepare a fair comparison before exploring each location.
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <div className={styles.fieldGrid}>
          <div className={styles.controlGroup}>
            <label className={styles.label} htmlFor="ai-locality-one">
              First locality
            </label>

            <input
              className={styles.input}
              id="ai-locality-one"
              value={first}
              onChange={(event) => {
                setFirst(event.currentTarget.value);
                setReady(false);
                setError("");
              }}
              maxLength={100}
              placeholder="e.g. Dubai Marina"
              required
            />
          </div>

          <div className={styles.controlGroup}>
            <label className={styles.label} htmlFor="ai-locality-two">
              Second locality
            </label>

            <input
              className={styles.input}
              id="ai-locality-two"
              value={second}
              onChange={(event) => {
                setSecond(event.currentTarget.value);
                setReady(false);
                setError("");
              }}
              maxLength={100}
              placeholder="e.g. Downtown Dubai"
              required
            />
          </div>
        </div>

        <div className={styles.inlineActions}>
          <button className={styles.buttonSecondary} type="submit">
            Prepare comparison checklist
          </button>
        </div>
      </form>

      {error ? (
        <p className={styles.inlineError} role="alert">
          {error}
        </p>
      ) : null}

      {ready ? (
        <div className={styles.localityResult} aria-live="polite">
          <div className={styles.localityPair}>
            <strong>{first.trim()}</strong>
            <span>vs</span>
            <strong>{second.trim()}</strong>
          </div>

          <ul className={styles.guidanceList}>
            <li>Compare costs for equivalent property types and sizes.</li>
            <li>
              Check commute, public transport, schools, healthcare and daily services.
            </li>
            <li>
              Verify available supply, maintenance, ownership and building rules.
            </li>
          </ul>

          <div className={styles.inlineActions}>
            <Link className={styles.textButton} href={searchHref(first)}>
              Search {first.trim()}
              <span aria-hidden="true">↗</span>
            </Link>

            <Link className={styles.textButton} href={searchHref(second)}>
              Search {second.trim()}
              <span aria-hidden="true">↗</span>
            </Link>
          </div>

          <p className={styles.disclosure}>
            This is a comparison framework, not a locality ranking. Current local facts must be checked independently.
          </p>
        </div>
      ) : null}
    </section>
  );
}
