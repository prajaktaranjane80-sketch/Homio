import styles from "./SystemComponents.module.css";

type Props = Readonly<{
  label?: string;
  reason?: string;
  basisVerified: boolean;
}>;

export function RecommendationBadge({
  label = "Recommended",
  reason,
  basisVerified,
}: Props) {
  return (
    <span
      className={`${styles.systemBadge} ${basisVerified ? styles.systemBadgeInfo : styles.systemBadgeWarning}`}
      title={reason || "Recommendation basis not supplied"}
    >
      <span className={styles.systemDot} aria-hidden="true" />
      {label}{basisVerified ? "" : " · Basis not verified"}
    </span>
  );
}
