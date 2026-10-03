"use client";

import { useState } from "react";
import styles from "./HomeIntentTabs.module.css";

const intents = ["Buy", "Rent", "Commercial", "Projects", "Land"];

export default function HomeIntentTabs() {
  const [activeIntent, setActiveIntent] = useState("Buy");

  return (
    <div className={styles.tabs} role="tablist" aria-label="Property intent">
      {intents.map((intent) => {
        const active = activeIntent === intent;

        return (
          <button
            key={intent}
            type="button"
            role="tab"
            aria-selected={active}
            className={`${styles.tab} ${active ? styles.active : ""}`}
            onClick={() => setActiveIntent(intent)}
          >
            {intent}
          </button>
        );
      })}
    </div>
  );
}
