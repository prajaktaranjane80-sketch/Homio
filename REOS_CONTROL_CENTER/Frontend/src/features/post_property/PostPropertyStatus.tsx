import { StatusBadge } from "@/components/system/StatusBadge";
import { LastUpdated } from "@/components/system/LastUpdated";

import styles from "./PostProperty.module.css";
import type { PostPropertyStatusRecord } from "./post-property.types";

type Props = Readonly<{
  record: PostPropertyStatusRecord;
}>;

const LABELS: Record<PostPropertyStatusRecord["state"], string> = {
  draft: "Draft",
  submitted: "Submitted",
  in_review: "In review",
  verified: "Verified by service",
  rejected: "Not approved",
  unavailable: "Status unavailable",
};

export default function PostPropertyStatus({ record }: Props) {
  const status =
    record.state === "verified"
      ? "success"
      : record.state === "rejected"
        ? "error"
        : record.state === "submitted" || record.state === "in_review"
          ? "pending"
          : record.state === "unavailable"
            ? "warning"
            : "neutral";

  return (
    <section className={styles.postPanel}>
      <header className={styles.postPanelHeader}>
        <h2 className={styles.postPanelTitle}>Submission status</h2>
        <p className={styles.postPanelDescription}>This state must reflect a result from the canonical property-submission service.</p>
      </header>

      <div className={`${styles.postState} ${record.state === "verified" ? styles.postSuccess : ""}`}>
        <span className={styles.postStateIcon} aria-hidden="true">
          {record.state === "verified" ? "✓" : record.state === "rejected" ? "!" : "◷"}
        </span>
        <div>
          <h3 className={styles.postStateTitle}>{LABELS[record.state]}</h3>
          {record.reference ? <p className={styles.postStateDescription}>Reference: {record.reference}</p> : null}
          {record.message ? <p className={styles.postStateDescription}>{record.message}</p> : null}
          {record.updatedAt ? <div style={{ marginTop: 9 }}><LastUpdated value={record.updatedAt} label="Service update" /></div> : null}
        </div>
      </div>

      <StatusBadge status={status} label={LABELS[record.state]} />

      <p className={styles.postNotice}>
        A submitted listing is not necessarily verified, approved, published or available for enquiries.
      </p>
    </section>
  );
}
