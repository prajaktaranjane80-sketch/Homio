import type { CompareFieldGroup, CompareItem } from "./compare.types";
import styles from "./SavedCompareExperience.module.css";

type CompareTableProps = Readonly<{ items: readonly CompareItem[]; selectedGroups: readonly CompareFieldGroup[]; onRemove?: (id: string) => void }>;

const displayValue = (value: string | number | null | undefined) => value === null || value === undefined || String(value).trim() === "" ? "Not supplied" : String(value);

export default function CompareTable({ items, selectedGroups, onRemove }: CompareTableProps) {
  const rows = new Map<string, { label: string; group: CompareFieldGroup; values: Map<string, string | number | null | undefined> }>();
  for (const item of items) for (const field of item.fields) {
    if (!selectedGroups.includes(field.group)) continue;
    const key = `${field.group}:${field.label.trim().toLocaleLowerCase()}`;
    if (!rows.has(key)) rows.set(key, { label: field.label, group: field.group, values: new Map() });
    rows.get(key)?.values.set(item.id, field.value);
  }
  if (items.length === 0) return null;
  if (rows.size === 0) return <div className={styles.tableNotice}>Choose at least one comparison group to show details.</div>;

  return <div className={styles.tableScroll} role="region" aria-label="Property and project comparison table" tabIndex={0}><table className={styles.compareTable}><thead><tr><th scope="col" className={styles.attributeHead}>Decision detail</th>{items.map((item) => <th scope="col" key={item.id}><div className={styles.compareColumn}><span className={styles.compareKind}>{item.kind}</span><strong>{item.title}</strong>{item.subtitle ? <span className={styles.compareSubtitle}>{item.subtitle}</span> : null}{item.href ? <a className={styles.columnLink} href={item.href}>Open details <span aria-hidden="true">↗</span></a> : null}{onRemove ? <button className={styles.quietAction} type="button" onClick={() => onRemove(item.id)} aria-label={`Remove ${item.title} from comparison`}>Remove</button> : null}</div></th>)}</tr></thead><tbody>{Array.from(rows.entries()).map(([key, row]) => <tr key={key}><th scope="row"><span className={styles.groupLabel}>{row.group}</span><strong>{row.label}</strong></th>{items.map((item) => { const value = row.values.get(item.id); const missing = value === undefined || value === null || String(value).trim() === ""; return <td key={item.id} className={missing ? styles.missingValue : undefined}>{displayValue(value)}</td>; })}</tr>)}</tbody></table></div>;
}
