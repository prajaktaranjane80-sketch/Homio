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
    <section className={styles.hero} aria-labelledby="homio-hero-title">
      <div className={`homio-container ${styles.container}`}>
        <div className={styles.content}>
          <span className={styles.eyebrow}>
            GLOBAL REAL ESTATE, ONE HOMIO
          </span>

          <h1 id="homio-hero-title" className={styles.title}>
            Find the right
            <br />
            place to live and invest.
          </h1>

          <p className={styles.description}>
            Discover homes, projects, commercial spaces and land across
            leading global markets, with HOMIO brokerage at the center of
            your journey.
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
