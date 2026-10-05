"use client";

import Link from "next/link";
import styles from "./SearchSuggestionPanel.module.css";

export type SearchSuggestion = {
  id: string;
  label: string;
  type: "city" | "locality" | "project" | "landmark";
  meta?: string;
  href?: string;
};

type SearchSuggestionPanelProps = Readonly<{
  suggestions: SearchSuggestion[];
  visible: boolean;
  onSelect?: (suggestion: SearchSuggestion) => void;
}>;

const typeLabels: Record<SearchSuggestion["type"], string> = {
  city: "City",
  locality: "Locality",
  project: "Project",
  landmark: "Landmark",
};

export default function SearchSuggestionPanel({
  suggestions,
  visible,
  onSelect,
}: SearchSuggestionPanelProps) {
  if (!visible || suggestions.length === 0) {
    return null;
  }

  return (
    <div className={styles.panel} role="listbox" aria-label="Search suggestions">
      <div className={styles.header}>
        <span>Suggestions</span>
      </div>

      <div className={styles.list}>
        {suggestions.map((suggestion) => {
          const content = (
            <>
              <span className={styles.icon} aria-hidden="true">
                ◎
              </span>

              <span className={styles.content}>
                <strong>{suggestion.label}</strong>

                <span className={styles.meta}>
                  {typeLabels[suggestion.type]}
                  {suggestion.meta ? ` · ${suggestion.meta}` : ""}
                </span>
              </span>
            </>
          );

          if (suggestion.href) {
            return (
              <Link
                key={suggestion.id}
                href={suggestion.href}
                className={styles.item}
                role="option"
                onClick={() => onSelect?.(suggestion)}
              >
                {content}
              </Link>
            );
          }

          return (
            <button
              key={suggestion.id}
              type="button"
              className={styles.item}
              role="option"
              onClick={() => onSelect?.(suggestion)}
            >
              {content}
            </button>
          );
        })}
      </div>
    </div>
  );
}
