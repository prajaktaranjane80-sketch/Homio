"use client";

import type {
  EnquiryHistoryItem,
  EnquiryStatus,
  EnquiryTargetKind,
} from "./enquiry.types";

import styles from "./EnquiryWorkspace.module.css";

type Props = Readonly<{
  items: readonly EnquiryHistoryItem[];
  isLoading?: boolean;
  error?: string;
  onRefresh?: () => void;
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

const TARGET_LABELS: Record<EnquiryTargetKind, string> = {
  property: "Property",
  project: "Project",
  general: "General enquiry",
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

export default function EnquiryHistory({
  items,
  isLoading = false,
  error,
  onRefresh,
}: Props) {
  // Only server-authorized records belong in the enquiry history.
  const historyItems = items.filter(
    (item) => item.source === "authorized_service",
  );

  return (
    <section
      className={styles.panel}
      aria-labelledby="enquiry-history-title"
    >
      <div className={styles.panelHeader}>
        <div className={styles.panelHeaderMain}>
          <p className={styles.kicker}>Your activity</p>

          <h2
            id="enquiry-history-title"
            className={styles.panelTitle}
          >
            Enquiry history
          </h2>

          <p className={styles.panelLead}>
            Review updates returned by the authorized enquiry
            service.
          </p>
        </div>

        {onRefresh ? (
          <button
            className={styles.secondaryButton}
            type="button"
            onClick={onRefresh}
            disabled={isLoading}
          >
            {isLoading ? "Refreshing…" : "Refresh"}
          </button>
        ) : null}
      </div>

      {error ? (
        <div className={styles.errorBanner} role="alert">
          {error}
        </div>
      ) : null}

      {isLoading && historyItems.length === 0 ? (
        <div className={styles.emptyState} role="status">
          <h3 className={styles.emptyTitle}>
            Loading enquiry history
          </h3>

          <p className={styles.emptyText}>
            Waiting for the authorized service to return your
            enquiry records.
          </p>
        </div>
      ) : historyItems.length === 0 ? (
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon} aria-hidden="true">
            ◷
          </div>

          <h3 className={styles.emptyTitle}>
            No service records available
          </h3>

          <p className={styles.emptyText}>
            Enquiry history will appear here when the authorized
            service is connected and returns records. Drafts from
            this local preview are not stored as enquiry history.
          </p>
        </div>
      ) : (
        <ol className={styles.timeline}>
          {historyItems.map((item) => {
            const targetTitle =
              item.target.title?.trim() ||
              `${TARGET_LABELS[item.target.kind]} enquiry`;

            const createdAt = formatDateTime(item.createdAt);
            const updatedAt = formatDateTime(item.updatedAt);

            return (
              <li className={styles.timelineItem} key={item.id}>
                <div
                  className={styles.timelineRail}
                  aria-hidden="true"
                >
                  <span className={styles.timelineDot} />
                </div>

                <div className={styles.stack}>
                  <div className={styles.statusHeading}>
                    <h3 className={styles.timelineTitle}>
                      {targetTitle}
                    </h3>

                    <span className={styles.badge}>
                      {STATUS_LABELS[item.status]}
                    </span>
                  </div>

                  {item.target.location ? (
                    <p className={styles.timelineDescription}>
                      {item.target.location}
                    </p>
                  ) : null}

                  <div className={styles.summaryList}>
                    {item.reference ? (
                      <div className={styles.summaryRow}>
                        <span className={styles.summaryLabel}>
                          Reference
                        </span>

                        <span className={styles.summaryValue}>
                          {item.reference}
                        </span>
                      </div>
                    ) : null}

                    {createdAt ? (
                      <div className={styles.summaryRow}>
                        <span className={styles.summaryLabel}>
                          Created
                        </span>

                        <span className={styles.summaryValue}>
                          {createdAt}
                        </span>
                      </div>
                    ) : null}

                    {updatedAt ? (
                      <div className={styles.summaryRow}>
                        <span className={styles.summaryLabel}>
                          Last updated
                        </span>

                        <span className={styles.summaryValue}>
                          {updatedAt}
                        </span>
                      </div>
                    ) : null}
                  </div>
                </div>
              </li>
            );
          })}
        </ol>
      )}
    </section>
  );
}
