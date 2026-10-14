"use client";

import type { FormEvent } from "react";

import styles from "./AIWorkspace.module.css";

type Props = Readonly<{
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
}>;

export default function AINaturalLanguageInput({
  value,
  onChange,
  onSubmit,
}: Props) {
  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit();
  }

  return (
    <section
      className={styles.card}
      aria-labelledby="ai-brief-title"
    >
      <div className={styles.cardHeader}>
        <div>
          <p className={styles.kicker}>Start with your own words</p>
          <h2 className={styles.cardTitle} id="ai-brief-title">
            Describe what matters to you
          </h2>
          <p className={styles.muted}>
            Start with the lifestyle, space and priorities that matter most.
          </p>
        </div>

        <span className={styles.cardGlyph} aria-hidden="true">
          ✳
        </span>
      </div>

      <form onSubmit={handleSubmit}>
        <label
          className={styles.srOnly}
          htmlFor="ai-natural-language-brief"
        >
          Your property brief
        </label>

        <textarea
          id="ai-natural-language-brief"
          className={styles.textArea}
          rows={4}
          value={value}
          maxLength={1200}
          onChange={(event) => {
            onChange(event.currentTarget.value);
          }}
          placeholder="For example: I need a quiet two-bedroom home near public transport, with outdoor space and a sustainable budget."
        />

        <div className={styles.composerFooter}>
          <span className={styles.fieldHelp}>
            This preview keeps your draft in page state. It is not sent to an AI service.
          </span>

          <button className={styles.buttonPrimary} type="submit">
            Build my brief
            <span aria-hidden="true">↗</span>
          </button>
        </div>
      </form>
    </section>
  );
}
