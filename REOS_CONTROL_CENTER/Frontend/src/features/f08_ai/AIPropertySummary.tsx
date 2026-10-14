"use client";

import { useState, type FormEvent } from "react";

import AIEmptyState from "./AIEmptyState";
import styles from "./AIWorkspace.module.css";

type Props = Readonly<{
  onDraftCreated: (draft: string) => void;
}>;

export default function AIPropertySummary({
  onDraftCreated,
}: Props) {
  const [details, setDetails] = useState("");
  const [prepared, setPrepared] = useState(false);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const value = details.trim();

    if (!value) {
      setPrepared(false);
      return;
    }

    setPrepared(true);
    onDraftCreated(value);
  }

  return (
    <section
      className={styles.card}
      aria-labelledby="ai-property-summary-title"
    >
      <div className={styles.cardHeader}>
        <div>
          <p className={styles.kicker}>Property notes</p>
          <h2 className={styles.cardTitle} id="ai-property-summary-title">
            Prepare a property brief
          </h2>
          <p className={styles.muted}>
            Keep your own notes and questions together.
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <label className={styles.label} htmlFor="ai-property-notes">
          Listing details or your notes
        </label>

        <textarea
          className={styles.textArea}
          id="ai-property-notes"
          rows={4}
          value={details}
          maxLength={2000}
          onChange={(event) => {
            setDetails(event.currentTarget.value);
            setPrepared(false);
          }}
          placeholder="Add the facts you want to verify, such as area, condition, fees and questions."
        />

        <div className={styles.inlineActions}>
          <button className={styles.buttonSecondary} type="submit">
            Keep as a local draft
          </button>

          <span className={styles.fieldHelp}>
            No text or file is sent to a model.
          </span>
        </div>
      </form>

      {prepared ? (
        <div className={styles.localDraft} aria-live="polite">
          <span className={styles.statusTag}>
            Draft prepared in this page
          </span>
          <p className={styles.localDraftText}>{details.trim()}</p>
          <p className={styles.disclosure}>
            This is your original text, not an AI-generated summary or verified property record.
          </p>
        </div>
      ) : (
        <AIEmptyState
          title="Keep facts separate from assumptions"
          description="Add the details you already have. A generated summary requires a connected, approved AI service."
        />
      )}
    </section>
  );
}
