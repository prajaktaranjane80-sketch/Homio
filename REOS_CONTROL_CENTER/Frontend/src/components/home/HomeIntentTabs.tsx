"use client";

import { useState } from "react";

const intents = [
  ["Buy", "buy"],
  ["Rent", "rent"],
  ["New Projects", "new-projects"],
  ["Commercial", "commercial"],
  ["PG", "pg"],
  ["Plot", "plot"],
] as const;

export function HomeIntentTabs() {
  const [activeIntent, setActiveIntent] = useState("buy");

  return (
    <div
      className="home-intent-tabs"
      aria-label="Choose property search intent"
    >
      {intents.map(([label, intent]) => (
        <button
          key={intent}
          type="button"
          className={
            activeIntent === intent
              ? "home-intent-tab home-intent-tab--active"
              : "home-intent-tab"
          }
          onClick={() => setActiveIntent(intent)}
          aria-pressed={activeIntent === intent}
        >
          {label}
        </button>
      ))}
    </div>
  );
}
