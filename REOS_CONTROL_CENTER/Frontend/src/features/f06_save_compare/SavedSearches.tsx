import type { SavedSearchRecord } from "./saved.types";
import SavedEmptyState from "./SavedEmptyState";
import styles from "./SavedCompareExperience.module.css";

type SavedSearchesProps = Readonly<{ items: readonly SavedSearchRecord[]; onRemove?: (id: string) => void }>;

export default function SavedSearches({ items, onRemove }: SavedSearchesProps) {
  if (!items.length) return <SavedEmptyState title="No saved searches yet" description="Saved filters and search intent will appear here when the approved search adapter supplies them." />;
  return <div className={styles.compactList}>{items.map((item) => (
    <article className={styles.compactRow} key={item.id}>
      <span className={styles.rowIcon} aria-hidden="true">⌕</span>
      <div className={styles.compactBody}><h3>{item.href ? <a href={item.href}>{item.title}</a> : item.title}</h3>{item.filtersSummary ? <p>{item.filtersSummary}</p> : <p>Search criteria not supplied</p>}<span className={styles.mutedLabel}>{item.updatedAt ? `Updated ${item.updatedAt}` : "Saved search"}</span></div>
      {onRemove ? <button type="button" className={styles.quietAction} onClick={() => onRemove(item.id)} aria-label={`Remove saved search ${item.title}`}>Remove</button> : null}
    </article>
  ))}</div>;
}
