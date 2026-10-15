"use client";

import { useState, type FormEvent } from "react";

import type {
  VisitActionDraft,
  VisitStatus,
} from "./visit.types";

import styles from "./EnquiryWorkspace.module.css";

type Props = Readonly<{
  reference: string;
  status: VisitStatus;
  onDraftReady?: (draft: VisitActionDraft) => void;
}>;

const CANCELLABLE_STATUSES: readonly VisitStatus[] = [
  "requested",
  "proposed",
  "confirmed",
  "reschedule_requested",
];

export default function VisitCancel({
  reference,
  status,
  onDraftReady,
}: Props) {
  const [reason, setReason] = useState("");
  const [error, setError] = useState("");
  const [draftReady, setDraftReady] = useState(false);

  const canRequestCancellation =
    Boolean(reference.trim()) &&
    CANCELLABLE_STATUSES.some((value) => value === status);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!reference.trim()) {
      setError(
        "A valid visit reference is required to prepare a cancellation request.",
      );
      setDraftReady(false);
      return;
    }

    if (!CANCELLABLE_STATUSES.some((value) => value === status)) {
      setError(
        "This visit status does not allow a new cancellation request. Check the latest visit status first.",
      );
      setDraftReady(false);
      return;
    }

    const draft: VisitActionDraft = {
      reference: reference.trim(),
      action: "cancel",
      reason: reason.trim(),
    };

    setError("");
    setDraftReady(true);
    onDraftReady?.(draft);
  }

  return (
    <section
      className={styles.panel}
      aria-labelledby="visit-cancel-heading"
    >
      <div className={styles.panelHeader}>
        <div className={styles.panelHeaderMain}>
          <p className={styles.kicker}>VISIT MANAGEMENT</p>

          <h2
            className={styles.panelTitle}
            id="visit-cancel-heading"
          >
            Request cancellation
          </h2>

          <p className={styles.panelLead}>
            Prepare a cancellation request for an existing visit.
            This preview does not cancel an appointment.
          </p>
        </div>
      </div>

      <form
        className={styles.form}
        onSubmit={handleSubmit}
        noValidate
      >
        <div className={styles.summaryList}>
          <div className={styles.summaryRow}>
            <span className={styles.summaryLabel}>
              Visit reference
            </span>

            <span className={styles.summaryValue}>
              {reference.trim() || "No reference supplied"}
            </span>
          </div>

          <div className={styles.summaryRow}>
            <span className={styles.summaryLabel}>
              Current status
            </span>

            <span className={styles.summaryValue}>
              {status.replaceAll("_", " ")}
            </span>
          </div>
        </div>

        {!canRequestCancellation ? (
          <div className={styles.notice} role="status">
            A cancellation draft cannot be prepared with the
            supplied reference and status. Use the latest
            authorized visit record before continuing.
          </div>
        ) : (
          <>
            <div className={styles.field}>
              <label
                className={styles.label}
                htmlFor="visit-cancel-reason"
              >
                Reason for cancellation
                <span className={styles.optional}>Optional</span>
              </label>

              <textarea
                className={styles.textarea}
                id="visit-cancel-reason"
                value={reason}
                rows={4}
                maxLength={1000}
                onChange={(event) => {
                  setReason(event.currentTarget.value);
                  setError("");
                  setDraftReady(false);
                }}
                placeholder="Share a reason if you would like to."
              />
            </div>

            <div className={styles.notice} role="note">
              Preparing this draft will not cancel the visit. A
              cancellation takes effect only after the authorized
              scheduling service processes the request and returns
              an updated status.
            </div>

            {error ? (
              <div className={styles.errorBanner} role="alert">
                {error}
              </div>
            ) : null}

            <div className={styles.formActions}>
              <button
                className={styles.primaryButton}
                type="submit"
              >
                Prepare cancellation draft
              </button>
            </div>
          </>
        )}
      </form>

      {draftReady ? (
        <div className={styles.successBanner} role="status" aria-live="polite">
          <strong>Cancellation draft prepared — not submitted.</strong>
          <p>
            Your visit has not been cancelled. No scheduling team
            was notified.
          </p>
        </div>
      ) : null}
    </section>
  );
}
