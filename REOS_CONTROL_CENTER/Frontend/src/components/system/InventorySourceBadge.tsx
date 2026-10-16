
/* File: src/components/system/InventorySourceBadge.tsx */
import styles from "./SharedSystem.module.css";

export type InventorySource =
  | "owner"
  | "builder"
  | "authorized-partner"
  | "homio"
  | "unknown";

const LABELS: Record<InventorySource, string> = {
  owner: "Owner supplied",
  builder: "Builder supplied",
  "authorized-partner": "Partner supplied",
  homio: "HOMIO managed",
  unknown: "Source not confirmed",
};

type Props = Readonly<{
  source: InventorySource;
  sourceVerified?: boolean;
}>;

export default function InventorySourceBadge({
  source,
  sourceVerified = false,
}: Props) {
  return (
    <span className={styles.sourceBadge}>
      {LABELS[source]}
      {sourceVerified ? " · Source checked" : " · Unverified"}
    </span>
  );
}
