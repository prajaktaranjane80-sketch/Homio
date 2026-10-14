"use client";

import type { SearchIntent } from "@/features/f03_search/search.types";

import styles from "./AIWorkspace.module.css";

type Props = Readonly<{
  onSelectPrompt: (
    prompt: string,
    intent?: SearchIntent,
  ) => void;
}>;

const DECISION_PROMPTS = [
  {
    title: "Clarify the must-haves",
    description:
      "Separate essentials from nice-to-haves before comparing listings.",
    prompt:
      "Help me separate essential property requirements from optional features.",
  },
  {
    title: "Check the total commitment",
    description:
      "List one-time, recurring and financing costs that need verification.",
    prompt:
      "Create a checklist of one-time, recurring and financing costs to verify before choosing a property.",
  },
  {
    title: "Prepare a viewing checklist",
    description:
      "Make inspections and follow-up questions consistent.",
    prompt:
      "Build a viewing checklist covering condition, light, noise, access, documents and questions to ask.",
  },
] as const;

export default function AIRecommendations({
  onSelectPrompt,
}: Props) {
  return (
    <section
      className={styles.card}
      aria-labelledby="ai-recommendations-title"
    >
      <div className={styles.cardHeader}>
        <div>
          <p className={styles.kicker}>Decision support</p>
          <h2 className={styles.cardTitle} id="ai-recommendations-title">
            Make the next step useful
          </h2>
        </div>
      </div>

      <div className={styles.recommendationStack}>
        {DECISION_PROMPTS.map((item, index) => (
          <article className={styles.recommendationCard} key={item.title}>
            <span className={styles.recommendationNumber}>
              {String(index + 1).padStart(2, "0")}
            </span>

            <div>
              <h3>{item.title}</h3>
              <p>{item.description}</p>

              <button
                className={styles.textButton}
                type="button"
                onClick={() => {
                  onSelectPrompt(item.prompt);
                }}
              >
                Use this checklist
                <span aria-hidden="true">↗</span>
              </button>
            </div>
          </article>
        ))}
      </div>

      <p className={styles.disclosure}>
        These are reusable prompts, not property-specific or AI-generated recommendations.
      </p>
    </section>
  );
}
