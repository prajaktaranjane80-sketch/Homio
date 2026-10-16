
/* File: src/components/system/LastUpdated.tsx */
import styles from "./SharedSystem.module.css";

type Props = Readonly<{
  value: string | null | undefined;
  sourceLabel?: string;
}>;

export default function LastUpdated({
  value,
  sourceLabel,
}: Props) {
  const timestamp = value ? new Date(value) : null;
  const valid =
    timestamp !== null &&
    Number.isFinite(timestamp.getTime());

  const formatted = valid
    ? new Intl.DateTimeFormat("en", {
        dateStyle: "medium",
        timeStyle: "short",
        timeZone: "UTC",
      }).format(timestamp)
    : "Update time unavailable";

  return (
    <span className={styles.lastUpdated}>
      <strong>Last updated:</strong>
      <time dateTime={valid ? timestamp.toISOString() : undefined}>
        {formatted}{valid ? " UTC" : ""}
      </time>
      {sourceLabel ? <span>· {sourceLabel}</span> : null}
    </span>
  );
}
