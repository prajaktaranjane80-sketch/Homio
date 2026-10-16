
/* File: src/components/system/VerificationBadge.tsx */
import styles from "./SharedSystem.module.css";

type Props = Readonly<{
  verified: boolean;
  label?: string;
}>;

export default function VerificationBadge({
  verified,
  label,
}: Props) {
  return (
    <span
      className={[
        styles.systemBadge,
        verified ? styles.badgePositive : styles.badgeWarning,
      ].join(" ")}
      aria-label={
        verified
          ? "Verification confirmed by the supplied source"
          : "Verification has not been confirmed"
      }
    >
      {verified ? label ?? "Verified" : label ?? "Not verified"}
    </span>
  );
}
