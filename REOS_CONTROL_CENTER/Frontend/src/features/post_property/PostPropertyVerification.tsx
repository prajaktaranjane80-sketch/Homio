import { VerificationBadge } from "@/components/system/VerificationBadge";

import styles from "./PostProperty.module.css";
import type { VerificationState } from "./post-property.types";

type Props = Readonly<{
  status: VerificationState;
  explanation?: string;
  reference?: string;
}>;

const LABELS: Record<VerificationState, string> = {
  not_started: "Verification not started",
  pending: "Verification pending",
  verified: "Verification verified by source",
  rejected: "Verification not approved",
  unavailable: "Verification service unavailable",
};

export default function PostPropertyVerification({
  status,
  explanation,
  reference,
}: Props) {
  const badgeStatus =
    status === "verified"
      ? "verified"
      : status === "rejected"
        ? "rejected"
        : status === "pending"
          ? "pending"
          : "unverified";

  return (
    <section className={styles.postPanel}>
      <header className={styles.postPanelHeader}>
        <h2 className={styles.postPanelTitle}>Property verification</h2>
        <p className={styles.postPanelDescription}>Verification status must come from the approved verification service.</p>
      </header>

      <div className={`${styles.postState} ${status === "verified" ? styles.postSuccess : ""}`}>
        <span className={styles.postStateIcon} aria-hidden="true">
          {status === "verified" ? "✓" : status === "rejected" ? "!" : "◷"}
        </span>
        <div>
          <h3 className={styles.postStateTitle}>{LABELS[status]}</h3>
          <p className={styles.postStateDescription}>
            {explanation ?? "No additional verification result was supplied."}
          </p>
          <div style={{ marginTop: 10 }}>
            <VerificationBadge status={badgeStatus} />
          </div>
          {reference ? <p className={styles.postStateDescription}>Reference: {reference}</p> : null}
        </div>
      </div>

      <p className={styles.postNotice}>
        A selected relationship, uploaded document or local form value cannot self-verify a property or its submitter.
      </p>
    </section>
  );
}
