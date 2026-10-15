"use client";

import type {
  EnquiryTarget,
} from "./enquiry.types";

import type {
  VisitStatus,
  VisitStatusSnapshot,
} from "./visit.types";

import styles from "./EnquiryWorkspace.module.css";

type Props = Readonly<{
  snapshot: VisitStatusSnapshot;
  target?: EnquiryTarget;
}>;

const STATUS_LABELS: Record<VisitStatus, string> = {
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
  if (!value) {
    return null;
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return null;
  }

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

export default function VisitConfirmation({
  snapshot,
  target,
}: Props) {
  const isLocalPreview = snapshot.source === "local_preview";

  const title = isLocalPreview
    ? "Your visit request draft is ready"
    : STATUS_LABELS[snapshot.status];

  const description = isLocalPreview
    ? "This is a preview only. Your request has not been sent and your visit has not been booked."
    : snapshot.message;

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

  return (
    <section
      className={styles.workspace}
      aria-labelledby="visit-confirmation-title"
    >
      <div className={styles.container}>
        <div className={styles.panel}>
          <div className={styles.statusPanel}>
            <p className={styles.kicker}>
              {isLocalPreview
                ? "Visit request preview"
                : "Visit request update"}
            </p>

            <div className={styles.statusHeading}>
              <div>
                <h1
                  id="visit-confirmation-title"
                  className={styles.statusTitle}
                >
                  {title}
                </h1>

                <p className={styles.statusText}>
                  {description}
                </p>
              </div>

              <span className={styles.badge}>
                {isLocalPreview
                  ? "Preview only"
                  : STATUS_LABELS[snapshot.status]}
              </span>
            </div>

            {target?.title ? (
              <div className={styles.summaryList}>
                <div className={styles.summaryRow}>
                  <span className={styles.summaryLabel}>
                    Visit for
                  </span>

                  <span className={styles.summaryValue}>
                    {target.title}
                  </span>
                </div>

                {target.location ? (
                  <div className={styles.summaryRow}>
                    <span className={styles.summaryLabel}>
                      Location
                    </span>

                    <span className={styles.summaryValue}>
                      {target.location}
                    </span>
                  </div>
                ) : null}
              </div>
            ) : null}

            {isLocalPreview ? (
              <div className={styles.notice} role="status">
                The authorized scheduling service is not connected
                in this preview. No appointment or reference has
                been created.
              </div>
            ) : (
              <>
                {snapshot.reference ? (
                  <div className={styles.summaryRow}>
                    <span className={styles.summaryLabel}>
                      Reference
                    </span>

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

                {snapshot.timeZone &&
                snapshot.status === "confirmed" ? (
                  <div className={styles.summaryRow}>
                    <span className={styles.summaryLabel}>
                      Time zone
                    </span>

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
              </>
            )}

            {target?.href ? (
              <div className={styles.formActions}>
                <a
                  className={styles.secondaryButton}
                  href={target.href}
                >
                  Return to listing
                </a>
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </section>
  );
}
