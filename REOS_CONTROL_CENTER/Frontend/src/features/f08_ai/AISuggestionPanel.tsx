"use client";

import type { SearchIntent } from "@/features/f03_search/search.types";

import { AI_PROMPT_SUGGESTIONS } from "./ai.constants";
import styles from "./AIWorkspace.module.css";

type Props = Readonly<{
  onSelectPrompt: (
    prompt: string,
    intent?: SearchIntent,
  ) => void;
}>;

export default function AISuggestionPanel({
  onSelectPrompt,
}: Props) {
  return (
    <section
      className={styles.card}
      aria-labelledby="ai-suggestions-title"
    >
      <div className={styles.cardHeader}>
        <div>
          <p className={styles.kicker}>A useful place to begin</p>
          <h2 className={styles.cardTitle} id="ai-suggestions-title">
            Explore a decision
          </h2>
        </div>
      </div>

      <div className={styles.suggestionList}>
        {AI_PROMPT_SUGGESTIONS.map((item) => (
          <button
            className={styles.suggestionButton}
            type="button"
            key={item.id}
            onClick={() => {
              onSelectPrompt(item.prompt, item.intent);
            }}
          >
            <span className={styles.suggestionGlyph} aria-hidden="true">
              {item.glyph}
            </span>

            <span className={styles.suggestionText}>
              <strong>{item.title}</strong>
              <span>{item.description}</span>
            </span>

            <span className={styles.suggestionArrow} aria-hidden="true">
              ↗
            </span>
          </button>
        ))}
      </div>
    </section>
  );
}
