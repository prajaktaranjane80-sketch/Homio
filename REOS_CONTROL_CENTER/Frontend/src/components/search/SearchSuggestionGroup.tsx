import Link from "next/link";

import styles from "./SearchExperience.module.css";
import type { SearchSuggestion } from "./SearchExperience.types";

type Props = Readonly<{
  heading: string;
  suggestions: readonly SearchSuggestion[];
  onSelect?: (suggestion: SearchSuggestion) => void;
}>;

export default function SearchSuggestionGroup({
  heading,
  suggestions,
  onSelect,
}: Props) {
  if (suggestions.length === 0) return null;

  return (
    <section className={styles.suggestionGroup} aria-label={heading}>
      <h3 className={styles.suggestionHeading}>{heading}</h3>

      {suggestions.map((item) => (
        <Link
          className={styles.searchItem}
          href={item.href}
          key={item.id}
          onClick={() => onSelect?.(item)}
        >
          <span className={styles.searchItemIcon} aria-hidden="true">
            {item.kind === "location"
              ? "⌖"
              : item.kind === "project"
                ? "▦"
                : item.kind === "property"
                  ? "⌂"
                  : item.kind === "recent"
                    ? "◷"
                    : "↗"}
          </span>
          <span className={styles.searchItemBody}>
            <span className={styles.searchItemTitle}>{item.title}</span>
            {item.description ? (
              <span className={styles.searchItemDescription}>{item.description}</span>
            ) : null}
          </span>
          <span className={styles.searchItemArrow} aria-hidden="true">↗</span>
        </Link>
      ))}
    </section>
  );
}
