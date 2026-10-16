import styles from "./SystemComponents.module.css";

type Props = Readonly<{
  sourceName: string;
  sourceType: "owner" | "developer" | "brokerage" | "partner" | "unknown";
  sourceVerified: boolean;
}>;

export function InventorySourceBadge({
  sourceName,
  sourceType,
  sourceVerified,
}: Props) {
  const safeName = sourceName.trim() || "Source not disclosed";
  const sourceLabels = {
    owner: "Owner-provided",
    developer: "Developer-provided",
    brokerage: "Brokerage-provided",
    partner: "Partner-provided",
    unknown: "Source unknown",
  } as const;

  return (
    <span
      className={`${styles.systemBadge} ${sourceVerified ? styles.systemBadgeGood : styles.systemBadgeWarning}`}
      title={`${sourceLabels[sourceType]} · ${safeName}`}
    >
      <span className={styles.systemDot} aria-hidden="true" />
      {sourceVerified ? "Source verified" : "Source not verified"} · {safeName}
    </span>
  );
}
