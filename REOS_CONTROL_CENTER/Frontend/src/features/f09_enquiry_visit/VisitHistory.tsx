"use client";

import type {
  EnquiryTarget,
  EnquiryTargetKind,
} from "./enquiry.types";

import type {
  VisitHistoryItem,
  VisitStatus,
} from "./visit.types";

import styles from "./EnquiryWorkspace.module.css";

type Props = Readonly<{
  items: readonly VisitHistoryItem[];
  isLoading?: boolean;
  error?: string;
  onRefresh?: () => void;
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

const TARGET_LABELS: Record<EnquiryTargetKind, string> = {
  property: "Property",
  project: "Project",
  general: "General enquiry",
};

function formatTimestamp(
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

function getTargetTitle(target: EnquiryTarget): string {
  return (
    target.title?.trim() ||
    `${TARGET_LABELS[target.kind]} visit`
  );
}

export default function VisitHistory({
  items,
  isLoading = false,
  error,
  onRefresh,
}: Props) {
  const historyItems = items.filter(
    (item) => item.source === "authorized_service",
  );

  return (
    <section
      className={styles.panel}
      aria-labelledby="visit-history-heading"
    >
      <div className={styles.panelHeader}>
        <div className={styles.panelHeaderMain}>
          <p className={styles.kicker}>YOUR ACTIVITY</p>

          <h2
            className={styles.panelTitle}
            id="visit-history-heading"
          >
            Visit history
          </h2>

          <p className={styles.panelLead}>
            Review visit requests and updates returned by the
            authorized scheduling service.
          </p>
        </div>

        {onRefresh ? (
          <button
            className={styles.secondaryButton}
            type="button"
            disabled={isLoading}
            onClick={onRefresh}
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
            Loading visit history
          </h3>

          <p className={styles.emptyText}>
            Waiting for the authorized scheduling service.
          </p>
        </div>
      ) : historyItems.length === 0 ? (
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon} aria-hidden="true">
            ◷
          </div>

          <h3 className={styles.emptyTitle}>
            No visit records available
          </h3>

          <p className={styles.emptyText}>
            Visit history will appear here when the authorized
            scheduling service returns records. Drafts created
            in this preview are not stored as visit history.
          </p>
        </div>
      ) : (
        <ol className={styles.timeline}>
          {historyItems.map((item) => {
            const title = getTargetTitle(item.target);

            const updatedAt = formatTimestamp(
              item.updatedAt,
              item.timeZone,
            );

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
                    <div>
                      <h3 className={styles.timelineTitle}>
                        {item.target.href ? (
                          <a href={item.target.href}>
                            {title}
                          </a>
                        ) : (
                          title
                        )}
                      </h3>

                      {item.target.location ? (
                        <p className={styles.timelineDescription}>
                          {item.target.location}
                        </p>
                      ) : null}
                    </div>

                    <span className={styles.badge}>
                      {STATUS_LABELS[item.status]}
                    </span>
                  </div>

                  <div className={styles.summaryList}>
                    <div className={styles.summaryRow}>
                      <span className={styles.summaryLabel}>
                        Preferred date
                      </span>

                      <span className={styles.summaryValue}>
                        {item.preferredDate || "Not provided"}
                      </span>
                    </div>

                    {item.timeZone ? (
                      <div className={styles.summaryRow}>
                        <span className={styles.summaryLabel}>
                          Time zone
                        </span>

                        <span className={styles.summaryValue}>
                          {item.timeZone}
                        </span>
                      </div>
                    ) : null}

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
