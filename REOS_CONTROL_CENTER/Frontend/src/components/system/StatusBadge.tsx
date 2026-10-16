import styles from "./SystemComponents.module.css";

type Props = Readonly<{
  status: "success" | "pending" | "warning" | "error" | "neutral" | "info";
  label: string;
}>;

export function StatusBadge({ status, label }: Props) {
  const tone = {
    success: styles.systemBadgeGood,
    pending: styles.systemBadgeWarning,
    warning: styles.systemBadgeWarning,
    error: styles.systemBadgeDanger,
    neutral: "",
    info: styles.systemBadgeInfo,
  }[status];

  return (
    <span className={`${styles.systemBadge} ${tone}`}>
      <span className={styles.systemDot} aria-hidden="true" />
      {label}
    </span>
  );
}
