import type { SavedRecord } from "./saved.types";
import SavedEmptyState from "./SavedEmptyState";
import styles from "./SavedCompareExperience.module.css";

type SavedPropertiesProps = Readonly<{
  items: readonly SavedRecord[];
  onRemove?: (id: string) => void;
}>;

export default function SavedProperties({ items, onRemove }: SavedPropertiesProps) {
  const properties = items.filter((item) => item.kind === "property");
  if (properties.length === 0) {
    return <SavedEmptyState title="No saved properties yet" description="When you save a property while exploring HOMIO, it will appear here so you can return to it without starting over." />;
  }

  return (
    <div className={styles.recordGrid}>
      {properties.map((item) => (
        <article className={styles.recordCard} key={item.id}>
          <div className={`${styles.recordArtwork} ${styles.propertyArtwork}`} aria-hidden="true"><span>PROPERTY</span><strong>⌂</strong></div>
          <div className={styles.recordBody}>
            <div className={styles.recordMeta}><span>PROPERTY</span>{item.statusLabel ? <span className={styles.statusChip}>{item.statusLabel}</span> : null}</div>
            <h3>{item.href ? <a href={item.href}>{item.title}</a> : item.title}</h3>
            {item.subtitle ? <p>{item.subtitle}</p> : null}
            {item.detailLine ? <p className={styles.detailLine}>{item.detailLine}</p> : null}
            <div className={styles.recordFooter}>
              {item.savedAt ? <span className={styles.mutedLabel}>Saved {item.savedAt}</span> : <span className={styles.mutedLabel}>Saved item</span>}
              {onRemove ? <button type="button" className={styles.quietAction} onClick={() => onRemove(item.id)} aria-label={`Remove ${item.title} from saved properties`}>Remove</button> : null}
            </div>
          </div>
        </article>
      ))}
    </div>
  );
}
