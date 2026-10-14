import type { SavedRecord } from "./saved.types";
import SavedEmptyState from "./SavedEmptyState";
import styles from "./SavedCompareExperience.module.css";

type SavedProjectsProps = Readonly<{ items: readonly SavedRecord[]; onRemove?: (id: string) => void }>;

export default function SavedProjects({ items, onRemove }: SavedProjectsProps) {
  const projects = items.filter((item) => item.kind === "project");
  if (!projects.length) return <SavedEmptyState title="No saved projects yet" description="Save a development or collection from a connected project experience to keep its context close at hand." />;
  return <div className={styles.recordGrid}>{projects.map((item) => (
    <article className={styles.recordCard} key={item.id}>
      <div className={`${styles.recordArtwork} ${styles.projectArtwork}`} aria-hidden="true"><span>PROJECT</span><strong>◇</strong></div>
      <div className={styles.recordBody}>
        <div className={styles.recordMeta}><span>PROJECT</span>{item.statusLabel ? <span className={styles.statusChip}>{item.statusLabel}</span> : null}</div>
        <h3>{item.href ? <a href={item.href}>{item.title}</a> : item.title}</h3>
        {item.subtitle ? <p>{item.subtitle}</p> : null}
        {item.detailLine ? <p className={styles.detailLine}>{item.detailLine}</p> : null}
        <div className={styles.recordFooter}><span className={styles.mutedLabel}>{item.savedAt ? `Saved ${item.savedAt}` : "Saved project"}</span>{onRemove ? <button type="button" className={styles.quietAction} onClick={() => onRemove(item.id)} aria-label={`Remove ${item.title} from saved projects`}>Remove</button> : null}</div>
      </div>
    </article>
  ))}</div>;
}
