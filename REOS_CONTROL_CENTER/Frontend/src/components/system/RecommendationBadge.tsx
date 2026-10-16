
/* File: src/components/system/RecommendationBadge.tsx */
import styles from "./SharedSystem.module.css";

type Props = Readonly<{
  label?: string;
  basis?: string;
}>;

export default function RecommendationBadge({
  label = "Suggested",
  basis,
}: Props) {
  return (
    <span
      className={styles.recommendationBadge}
      title={basis}
      aria-label={
        basis ? `${label}. Basis: ${basis}` : `${label}. Basis not specified`
      }
    >
      <span aria-hidden="true">✦</span>
      {label}
    </span>
  );
}
