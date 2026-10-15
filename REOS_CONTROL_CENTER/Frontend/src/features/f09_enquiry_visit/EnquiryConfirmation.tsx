"use client";

import type {
  EnquiryStatus,
  EnquiryStatusSnapshot,
  EnquiryTarget,
} from "./enquiry.types";

import styles from "./EnquiryWorkspace.module.css";

type Props = Readonly<{
  snapshot: EnquiryStatusSnapshot;
  target?: EnquiryTarget;
}>;

const STATUS_LABELS: Record<EnquiryStatus, string> = {
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

export default function EnquiryConfirmation({
  snapshot,
  target,
}: Props) {
  const isLocalPreview = snapshot.source === "local_preview";

  const title = isLocalPreview
    ? "Your enquiry draft is ready"
    : STATUS_LABELS[snapshot.status];

  const description = isLocalPreview
    ? "This is a local preview only. Your enquiry has not been sent, no reference has been created, and no broker has been notified."
    : snapshot.message;

  const updatedAt = formatDateTime(snapshot.updatedAt);

  return (
    <section
      className={styles.workspace}
      aria-labelledby="enquiry-confirmation-title"
    >
      <div className={styles.container}>
        <div className={styles.panel}>
          <div className={styles.statusPanel}>
            <p className={styles.kicker}>
              {isLocalPreview
                ? "Enquiry preview"
                : "Enquiry update"}
            </p>

            <div className={styles.statusHeading}>
              <div>
                <h1
                  id="enquiry-confirmation-title"
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
                    Enquiry for
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
                Review is available in this preview. Sending the
                enquiry requires the authorized enquiry service.
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
