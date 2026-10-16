import styles from "./SystemComponents.module.css";

type Props = Readonly<{
  status: "verified" | "pending" | "unverified" | "rejected";
  label?: string;
}>;

export function VerificationBadge({ status, label }: Props) {
  const tone =
    status === "verified"
      ? styles.systemBadgeGood
      : status === "rejected"
        ? styles.systemBadgeDanger
        : styles.systemBadgeWarning;

  const text = label ?? ({
    verified: "Verified by source",
    pending: "Verification pending",
    unverified: "Not verified",
    rejected: "Verification not approved",
  } as const)[status];

  return (
    <span className={`${styles.systemBadge} ${tone}`} aria-label={`Verification: ${text}`}>
      <span className={styles.systemDot} aria-hidden="true" />
      {text}
    </span>
  );
}
