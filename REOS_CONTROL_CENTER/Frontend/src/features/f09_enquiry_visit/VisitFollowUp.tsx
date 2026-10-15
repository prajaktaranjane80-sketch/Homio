"use client";

import { useState, type FormEvent } from "react";

import type { VisitStatus } from "./visit.types";
import styles from "./EnquiryWorkspace.module.css";

export type VisitFollowUpDraft = Readonly<{
  reference: string;
  outcome:
    | "interested"
    | "need_more_information"
    | "follow_up_requested"
    | "not_interested";
  rating?: number;
  message: string;
}>;

type Props = Readonly<{
  reference: string;
  status: VisitStatus;
  onDraftReady?: (draft: VisitFollowUpDraft) => void;
}>;

const OUTCOME_OPTIONS: ReadonlyArray<{
  value: VisitFollowUpDraft["outcome"];
  label: string;
}> = [
  { value: "interested", label: "I am interested in proceeding" },
  {
    value: "need_more_information",
    label: "I need more information",
  },
  {
    value: "follow_up_requested",
    label: "I would like a follow-up",
  },
  { value: "not_interested", label: "This is not the right fit" },
];

export default function VisitFollowUp({
  reference,
  status,
  onDraftReady,
}: Props) {
  const [outcome, setOutcome] =
    useState<VisitFollowUpDraft["outcome"]>("interested");
  const [rating, setRating] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [draftReady, setDraftReady] = useState(false);

  const canPrepareFollowUp =
    Boolean(reference.trim()) && status === "completed";

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!reference.trim()) {
      setError("A visit reference is required.");
      setDraftReady(false);
      return;
    }

    if (status !== "completed") {
      setError(
        "Follow-up feedback is available after the visit is marked completed by the authorized service.",
      );
      setDraftReady(false);
      return;
    }

    const parsedRating = rating ? Number(rating) : undefined;

    if (
      parsedRating !== undefined &&
      (!Number.isInteger(parsedRating) ||
        parsedRating < 1 ||
        parsedRating > 5)
    ) {
      setError("Choose a rating between 1 and 5.");
      setDraftReady(false);
      return;
    }

    const draft: VisitFollowUpDraft = {
      reference: reference.trim(),
      outcome,
      ...(parsedRating !== undefined
        ? { rating: parsedRating }
        : {}),
      message: message.trim(),
    };

    setError("");
    setDraftReady(true);
    onDraftReady?.(draft);
  }

  return (
    <section
      className={styles.panel}
      aria-labelledby="visit-follow-up-heading"
    >
      <div className={styles.panelHeader}>
        <div className={styles.panelHeaderMain}>
          <p className={styles.kicker}>AFTER YOUR VISIT</p>

          <h2
            className={styles.panelTitle}
            id="visit-follow-up-heading"
          >
            Share your feedback
          </h2>

          <p className={styles.panelLead}>
            Record your feedback or next-step preference. This
            preview does not send feedback to an agent or broker.
          </p>
        </div>
      </div>

      {!canPrepareFollowUp ? (
        <div className={styles.notice} role="status">
          Follow-up draft preparation requires a visit reference
          and a completed status returned by the authorized
          scheduling service.
        </div>
      ) : (
        <form
          className={styles.form}
          onSubmit={handleSubmit}
          noValidate
        >
          <div className={styles.summaryRow}>
            <span className={styles.summaryLabel}>
              Visit reference
            </span>
            <span className={styles.summaryValue}>
              {reference.trim()}
            </span>
          </div>

          <div className={styles.field}>
            <label
              className={styles.label}
              htmlFor="visit-follow-up-outcome"
            >
              What would you like to do next?
            </label>

            <select
              className={styles.select}
              id="visit-follow-up-outcome"
              value={outcome}
              onChange={(event) => {
                setOutcome(
                  event.currentTarget.value as VisitFollowUpDraft["outcome"],
                );
                setDraftReady(false);
                setError("");
              }}
            >
              {OUTCOME_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div className={styles.field}>
            <label
              className={styles.label}
              htmlFor="visit-follow-up-rating"
            >
              How was your visit?
              <span className={styles.optional}>Optional</span>
            </label>

            <select
              className={styles.select}
              id="visit-follow-up-rating"
              value={rating}
              onChange={(event) => {
                setRating(event.currentTarget.value);
                setDraftReady(false);
                setError("");
              }}
            >
              <option value="">Skip rating</option>
              <option value="5">5 — Excellent</option>
              <option value="4">4 — Very good</option>
              <option value="3">3 — Good</option>
              <option value="2">2 — Could be better</option>
              <option value="1">1 — Poor</option>
            </select>
          </div>

          <div className={styles.field}>
            <label
              className={styles.label}
              htmlFor="visit-follow-up-message"
            >
              Additional feedback
              <span className={styles.optional}>Optional</span>
            </label>

            <textarea
              className={styles.textarea}
              id="visit-follow-up-message"
              value={message}
              rows={4}
              maxLength={2000}
              onChange={(event) => {
                setMessage(event.currentTarget.value);
                setDraftReady(false);
                setError("");
              }}
              placeholder="Share questions, feedback, or the next step you prefer."
            />
          </div>

          {error ? (
            <div className={styles.errorBanner} role="alert">
              {error}
            </div>
          ) : null}

          <div className={styles.notice} role="note">
            This is a local draft only. It will not be sent or
            stored by a follow-up service in the current preview.
          </div>

          <div className={styles.formActions}>
            <button className={styles.primaryButton} type="submit">
              Prepare follow-up draft
            </button>
          </div>
        </form>
      )}

      {draftReady ? (
        <div
          className={styles.successBanner}
          role="status"
          aria-live="polite"
        >
          <strong>Follow-up draft prepared — not sent.</strong>
          <p>
            No agent or broker was notified, and the feedback has
            not been saved to a service.
          </p>
        </div>
      ) : null}
    </section>
  );
}
