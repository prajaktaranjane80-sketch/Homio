import styles from "./SearchResultCount.module.css";

type SearchResultCountProps = Readonly<{
  total: number;
  page: number;
  pageSize: number;
  entityLabel?: string;
}>;

export default function SearchResultCount({
  total,
  page,
  pageSize,
  entityLabel = "properties",
}: SearchResultCountProps) {
  const safePage = Math.max(1, page);
  const start = total === 0 ? 0 : (safePage - 1) * pageSize + 1;
  const end = Math.min(safePage * pageSize, total);

  return (
    <p className={styles.count} aria-live="polite">
      Showing <strong>{start.toLocaleString()}</strong>–
      <strong>{end.toLocaleString()}</strong> of{" "}
      <strong>{total.toLocaleString()}</strong> {entityLabel}
    </p>
  );
}
