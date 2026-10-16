import styles from "./SystemComponents.module.css";

type Props = Readonly<{
  value: string | null | undefined;
  label?: string;
}>;

export function LastUpdated({ value, label = "Last updated" }: Props) {
  const timestamp = value ? Date.parse(value) : Number.NaN;
  const valid = Number.isFinite(timestamp);

  const formatted = valid
    ? new Intl.DateTimeFormat("en", {
        dateStyle: "medium",
        timeStyle: "short",
        timeZone: "UTC",
      }).format(timestamp)
    : "Update time unavailable";

  return (
    <span className={styles.systemTimestamp}>
      <span aria-hidden="true">◷</span>
      <span>{label}: </span>
      {valid ? (
        <time dateTime={new Date(timestamp).toISOString()}>{formatted} UTC</time>
      ) : (
        <span>{formatted}</span>
      )}
    </span>
  );
}
