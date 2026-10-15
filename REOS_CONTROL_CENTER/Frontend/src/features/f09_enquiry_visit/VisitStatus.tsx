"use client";

import type { VisitStatus as VisitStatusValue, VisitStatusSnapshot } from "./visit.types";
import styles from "./EnquiryWorkspace.module.css";

type Props = Readonly<{
  snapshot?: VisitStatusSnapshot | null;
  heading?: string;
}>;

const STATUS_LABELS: Record<VisitStatusValue, string> = {
  draft: "Draft",
  ready_to_submit: "Ready for review",
  requested: "Request received",
  proposed: "Alternative time proposed",
  confirmed: "Visit confirmed",
  reschedule_requested: "Reschedule requested",
  cancel_requested: "Cancellation requested",
  cancelled: "Visit cancelled",
  completed: "Visit completed",
  declined: "Request declined",
  submission_unavailable: "Not booked",
};

function formatDateTime(
  value?: string,
  timeZone?: string,
): string | null {
  if (!value) return null;

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;

  try {
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
      ...(timeZone ? { timeZone } : {}),
    }).format(date);
  } catch {
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(date);
  }
}

export default function VisitStatus({
  snapshot,
  heading = "Visit status",
}: Props) {
  if (!snapshot) {
    return (
      <section
        className={styles.statusPanel}
        aria-labelledby="visit-status-heading"
      >
        <h2
          id="visit-status-heading"
          className={styles.statusTitle}
        >
          {heading}
        </h2>

        <p className={styles.statusText}>
          No visit status is available yet.
        </p>

        <p className={styles.fieldHelp}>
          A status will appear when an authorized scheduling
          service returns an update.
        </p>
      </section>
    );
  }

  const isLocalPreview = snapshot.source === "local_preview";

  const displayStatus = isLocalPreview
    ? "Local draft — not booked"
    : STATUS_LABELS[snapshot.status];

  const confirmedDateTime =
    !isLocalPreview && snapshot.status === "confirmed"
      ? formatDateTime(
          snapshot.confirmedDateTime,
          snapshot.timeZone,
        )
      : null;

  const confirmedAt =
    !isLocalPreview && snapshot.status === "confirmed"
      ? formatDateTime(snapshot.confirmedAt, snapshot.timeZone)
      : null;

  const updatedAt = !isLocalPreview
    ? formatDateTime(snapshot.updatedAt, snapshot.timeZone)
    : null;

  const isUnavailable =
    !isLocalPreview &&
    (
      snapshot.status === "submission_unavailable" ||
      snapshot.status === "declined"
    );

  const isConfirmed =
    !isLocalPreview &&
    (
      snapshot.status === "confirmed" ||
      snapshot.status === "completed"
    );

  const messageClass = isLocalPreview
    ? styles.notice
    : isUnavailable
      ? styles.errorBanner
      : isConfirmed
        ? styles.successBanner
        : styles.notice;

  return (
    <section
      className={styles.statusPanel}
      aria-labelledby="visit-status-heading"
      aria-live="polite"
    >
      <div className={styles.statusHeading}>
        <div>
          <p className={styles.kicker}>
            {isLocalPreview ? "Preview status" : "Service status"}
          </p>

          <h2
            id="visit-status-heading"
            className={styles.statusTitle}
          >
            {heading}
          </h2>
        </div>

        <span className={styles.badge}>{displayStatus}</span>
      </div>

      <div className={messageClass} role="status">
        {isLocalPreview
          ? "The visit request has not been sent. The authorized scheduling service is not connected in this preview."
          : snapshot.message}
      </div>

      {!isLocalPreview && snapshot.reference ? (
        <div className={styles.summaryRow}>
          <span className={styles.summaryLabel}>Reference</span>
          <span className={styles.summaryValue}>
            {snapshot.reference}
          </span>
        </div>
      ) : null}

      {confirmedDateTime ? (
        <div className={styles.summaryRow}>
          <span className={styles.summaryLabel}>
            Confirmed visit
          </span>
          <span className={styles.summaryValue}>
            {confirmedDateTime}
          </span>
        </div>
      ) : null}

      {!isLocalPreview && snapshot.timeZone ? (
        <div className={styles.summaryRow}>
          <span className={styles.summaryLabel}>Time zone</span>
          <span className={styles.summaryValue}>
            {snapshot.timeZone}
          </span>
        </div>
      ) : null}

      {confirmedAt ? (
        <p className={styles.fieldHelp}>
          Confirmation received {confirmedAt}
        </p>
      ) : null}

      {updatedAt ? (
        <p className={styles.fieldHelp}>
          Last updated {updatedAt}
        </p>
      ) : null}
    </section>
  );
}
