import type { SavedRecord } from "./saved.types";
import SavedEmptyState from "./SavedEmptyState";
import styles from "./SavedCompareExperience.module.css";

type SavedLocalitiesProps = Readonly<{ items: readonly SavedRecord[]; onRemove?: (id: string) => void }>;

export default function SavedLocalities({ items, onRemove }: SavedLocalitiesProps) {
  const localities = items.filter((item) => item.kind === "locality");
  if (!localities.length) return <SavedEmptyState title="No saved locations yet" description="Keep neighbourhoods and locations together as your search evolves across cities and markets." />;
  return <div className={styles.recordGrid}>{localities.map((item) => (
    <article className={styles.recordCard} key={item.id}>
      <div className={`${styles.recordArtwork} ${styles.localityArtwork}`} aria-hidden="true"><span>LOCATION</span><strong>◎</strong></div>
      <div className={styles.recordBody}>
        <div className={styles.recordMeta}><span>LOCALITY</span>{item.statusLabel ? <span className={styles.statusChip}>{item.statusLabel}</span> : null}</div>
        <h3>{item.href ? <a href={item.href}>{item.title}</a> : item.title}</h3>
        {item.subtitle ? <p>{item.subtitle}</p> : null}
        {item.detailLine ? <p className={styles.detailLine}>{item.detailLine}</p> : null}
        <div className={styles.recordFooter}><span className={styles.mutedLabel}>{item.savedAt ? `Saved ${item.savedAt}` : "Saved location"}</span>{onRemove ? <button type="button" className={styles.quietAction} onClick={() => onRemove(item.id)} aria-label={`Remove ${item.title} from saved locations`}>Remove</button> : null}</div>
      </div>
    </article>
  ))}</div>;
}
