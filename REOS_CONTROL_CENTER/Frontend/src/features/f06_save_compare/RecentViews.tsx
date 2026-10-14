import type { RecentViewRecord } from "./saved.types";
import SavedEmptyState from "./SavedEmptyState";
import styles from "./SavedCompareExperience.module.css";

type RecentViewsProps = Readonly<{ items: readonly RecentViewRecord[] }>;

const kindLabels = { property: "PROPERTY", project: "PROJECT", locality: "LOCALITY" } as const;

export default function RecentViews({ items }: RecentViewsProps) {
  if (!items.length) return <SavedEmptyState title="Your recent views will appear here" description="Once a history adapter is connected, you can resume places and opportunities you recently explored." />;
  return <div className={styles.compactList}>{items.map((item) => (
    <article className={styles.compactRow} key={item.id}>
      <span className={styles.rowIcon} aria-hidden="true">↗</span>
      <div className={styles.compactBody}><div className={styles.recordMeta}><span>{kindLabels[item.kind]}</span></div><h3>{item.href ? <a href={item.href}>{item.title}</a> : item.title}</h3>{item.subtitle ? <p>{item.subtitle}</p> : null}<span className={styles.mutedLabel}>{item.viewedAt ? `Viewed ${item.viewedAt}` : "Recent view"}</span></div>
      {item.href ? <a className={styles.outlineAction} href={item.href}>Return <span aria-hidden="true">↗</span></a> : <span className={styles.mutedLabel}>Destination unavailable</span>}
    </article>
  ))}</div>;
}
