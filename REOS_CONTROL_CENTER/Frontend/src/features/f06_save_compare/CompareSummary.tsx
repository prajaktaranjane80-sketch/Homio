import type { CompareItem } from "./compare.types";
import styles from "./SavedCompareExperience.module.css";

type CompareSummaryProps = Readonly<{ items: readonly CompareItem[] }>;

export default function CompareSummary({ items }: CompareSummaryProps) {
  const kinds = Array.from(new Set(items.map((item) => item.kind)));
  const label = kinds.length === 0 ? "No options" : kinds.length === 1 ? `${items.length} ${kinds[0]}${items.length === 1 ? "" : "s"}` : `${items.length} options`;
  return <div className={styles.compareSummary}><span className={styles.summaryGlyph} aria-hidden="true">⇄</span><div><strong>{label} in focus</strong><p>Compare supplied facts side by side. Missing information stays visible as missing.</p></div><span className={styles.summaryCount}>{String(items.length).padStart(2, "0")}</span></div>;
}
