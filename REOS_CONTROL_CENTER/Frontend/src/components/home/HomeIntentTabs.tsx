"use client";

import type { HomeIntent } from "./HomeHero";
import styles from "./HomeIntentTabs.module.css";

const intents: Array<{
  label: string;
  value: HomeIntent;
}> = [
  { label: "Buy", value: "buy" },
  { label: "Rent", value: "rent" },
  { label: "Commercial", value: "commercial" },
  { label: "Projects", value: "projects" },
  { label: "Land", value: "land" },
];

type HomeIntentTabsProps = Readonly<{
  activeIntent: HomeIntent;
  onIntentChange: (intent: HomeIntent) => void;
}>;

export default function HomeIntentTabs({
  activeIntent,
  onIntentChange,
}: HomeIntentTabsProps) {
  return (
    <div
      className={styles.tabs}
      role="tablist"
      aria-label="Property intent"
    >
      {intents.map((intent) => {
        const active = activeIntent === intent.value;

        return (
          <button
            key={intent.value}
            type="button"
            role="tab"
            aria-selected={active}
            className={`${styles.tab} ${active ? styles.active : ""}`}
            onClick={() => onIntentChange(intent.value)}
          >
            {intent.label}
          </button>
        );
      })}
    </div>
  );
}
