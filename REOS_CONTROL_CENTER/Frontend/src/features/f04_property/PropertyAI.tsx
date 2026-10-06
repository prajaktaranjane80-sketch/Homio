"use client";

import { useState } from "react";
import styles from "./PropertyAI.module.css";

const prompts = [
  "What should I know before enquiring?",
  "How does this property compare with a similar one?",
  "Help me understand the location.",
];

export default function PropertyAI() {
  const [activePrompt, setActivePrompt] = useState<string>();

  return (
    <section className={styles.section}>
      <div className={styles.header}>
        <div>
          <span className={styles.eyebrow}>HOMIO AI</span>
          <h2>Get context before you decide.</h2>
          <p>
            Ask questions about the property experience without replacing
            authoritative REOS information.
          </p>
        </div>

        <span className={styles.badge}>AI ASSIST</span>
      </div>

      <div className={styles.promptGrid}>
        {prompts.map((prompt) => (
          <button
            key={prompt}
            type="button"
            className={`${styles.prompt} ${
              activePrompt === prompt ? styles.active : ""
            }`}
            onClick={() => setActivePrompt(prompt)}
          >
            <span>{prompt}</span>
            <strong aria-hidden="true">→</strong>
          </button>
        ))}
      </div>

      {activePrompt ? (
        <div className={styles.response}>
          <span>HOMIO AI</span>
          <p>
            {activePrompt} This experience surface is ready for the
            verified AI capability to provide the authoritative answer.
          </p>
        </div>
      ) : null}
    </section>
  );
}
