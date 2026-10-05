import styles from "./SearchResultCount.module.css";

type SearchResultCountProps = Readonly<{
  total: number;
  page: number;
  pageSize: number;
}>;

export default function SearchResultCount({
  total,
  page,
  pageSize,
}: SearchResultCountProps) {
  const start = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const end = Math.min(page * pageSize, total);

  return (
    <p className={styles.count}>
      Showing <strong>{start.toLocaleString()}</strong>–
      <strong>{end.toLocaleString()}</strong> of{" "}
      <strong>{total.toLocaleString()}</strong> properties
    </p>
  );
}
