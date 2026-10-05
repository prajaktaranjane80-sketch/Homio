"use client";

import type { SearchIntent } from "./search.types";
import styles from "./SearchIntentTabs.module.css";

type SearchIntentTabsProps = Readonly<{
  intents: SearchIntent[];
  activeIntent: SearchIntent;
  onChange: (intent: SearchIntent) => void;
}>;

const labels: Record<SearchIntent, string> = {
  buy: "Buy",
  rent: "Rent",
  commercial: "Commercial",
  projects: "Projects",
  land: "Land",
};

export default function SearchIntentTabs({
  intents,
  activeIntent,
  onChange,
}: SearchIntentTabsProps) {
  return (
    <div
      className={styles.tabs}
      role="tablist"
      aria-label="Property search intent"
    >
      {intents.map((intent) => {
        const active = intent === activeIntent;

        return (
          <button
            key={intent}
            type="button"
            role="tab"
            aria-selected={active}
            className={`${styles.tab} ${active ? styles.active : ""}`}
            onClick={() => onChange(intent)}
          >
            {labels[intent]}
          </button>
        );
      })}
    </div>
  );
}
