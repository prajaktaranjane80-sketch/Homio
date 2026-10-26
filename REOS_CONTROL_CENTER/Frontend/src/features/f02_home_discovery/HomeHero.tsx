"use client";

import { useState } from "react";

import HomeIntentTabs from "./HomeIntentTabs";
import HomeSearch from "./HomeSearch";
import styles from "./HomeHero.module.css";

export type HomeIntent =
  | "buy"
  | "rent"
  | "commercial"
  | "projects"
  | "land";

export default function HomeHero() {
  const [activeIntent, setActiveIntent] =
    useState<HomeIntent>("buy");

  return (
    <section
      className={styles.hero}
      aria-labelledby="homio-hero-title"
    >
      <div className={`homio-container ${styles.container}`}>
        <div className={styles.content}>
          <span className={styles.eyebrow}>
            PUNE-FIRST PROPERTY DISCOVERY
          </span>

          <h1 id="homio-hero-title" className={styles.title}>
            Find your next place
            <br />
            in Pune.
          </h1>

          <p className={styles.description}>
            Start with a Pune-focused search across homes, rentals,
            projects and commercial spaces. Review property information
            and source status before taking the next step.
          </p>

          <div className={styles.searchArea}>
            <HomeIntentTabs
              activeIntent={activeIntent}
              onIntentChange={setActiveIntent}
            />

            <HomeSearch intent={activeIntent} />
          </div>
        </div>
      </div>
    </section>
  );
}
