"use client";

import type {
  EnquiryStatus as EnquiryStatusValue,
  EnquiryStatusSnapshot,
} from "./enquiry.types";

import styles from "./EnquiryWorkspace.module.css";

type Props = Readonly<{
  snapshot?: EnquiryStatusSnapshot | null;
  heading?: string;
}>;

const STATUS_LABELS: Record<EnquiryStatusValue, string> = {
  draft: "Draft",
  ready_to_submit: "Ready for review",
  submitted: "Submitted",
  acknowledged: "Acknowledged",
  in_progress: "In progress",
  responded: "Response received",
  closed: "Closed",
  submission_unavailable: "Not sent",
};

function formatDateTime(value?: string): string | null {
  if (!value) {
    return null;
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return null;
  }

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

export default function EnquiryStatus({
  snapshot,
  heading = "Enquiry status",
}: Props) {
  if (!snapshot) {
    return (
      <section
        className={styles.statusPanel}
        aria-labelledby="enquiry-status-title"
      >
        <h2
          id="enquiry-status-title"
          className={styles.statusTitle}
        >
          {heading}
        </h2>

        <p className={styles.statusText}>
          No enquiry status is available yet.
        </p>

        <p className={styles.fieldHelp}>
          A status will appear when an enquiry draft is prepared or
          an authorized service returns an update.
        </p>
      </section>
    );
  }

  const isLocalPreview = snapshot.source === "local_preview";

  const displayStatus = isLocalPreview
    ? snapshot.status === "ready_to_submit"
      ? "Draft ready for review"
      : "Local draft"
    : STATUS_LABELS[snapshot.status];

  const updatedAt = formatDateTime(snapshot.updatedAt);

  const statusClass =
    !isLocalPreview &&
    snapshot.status === "submission_unavailable"
      ? styles.errorBanner
      : !isLocalPreview &&
          [
            "submitted",
            "acknowledged",
            "responded",
          ].includes(snapshot.status)
        ? styles.successBanner
        : styles.notice;

  return (
    <section
      className={styles.statusPanel}
      aria-labelledby="enquiry-status-title"
      aria-live="polite"
    >
      <div className={styles.statusHeading}>
        <div>
          <p className={styles.kicker}>
            {isLocalPreview
              ? "Preview status"
              : "Service status"}
          </p>

          <h2
            id="enquiry-status-title"
            className={styles.statusTitle}
          >
            {heading}
          </h2>
        </div>

        <span className={styles.badge}>{displayStatus}</span>
      </div>

      <div className={statusClass} role="status">
        {isLocalPreview
          ? "This enquiry has not been sent. The authorized enquiry service is not connected in this preview."
          : snapshot.message}
      </div>

      {!isLocalPreview && snapshot.reference ? (
        <div className={styles.summaryRow}>
          <span className={styles.summaryLabel}>
            Reference
          </span>

          <span className={styles.summaryValue}>
            {snapshot.reference}
          </span>
        </div>
      ) : null}

      {updatedAt ? (
        <p className={styles.fieldHelp}>
          Last updated {updatedAt}
        </p>
      ) : null}
    </section>
  );
}
