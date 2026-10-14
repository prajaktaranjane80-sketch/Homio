"use client";

import { useMemo, useState } from "react";
import type { CompareCategory, CompareFieldGroup, CompareItem } from "./compare.types";
import { COMPARE_FIELD_GROUPS, COMPARE_MAX_ITEMS } from "./compare.types";
import CompareActions from "./CompareActions";
import CompareCriteria from "./CompareCriteria";
import CompareEmptyState from "./CompareEmptyState";
import CompareLocalities from "./CompareLocalities";
import CompareProperties from "./CompareProperties";
import CompareProjects from "./CompareProjects";
import CompareSummary from "./CompareSummary";
import CompareTable from "./CompareTable";
import styles from "./SavedCompareExperience.module.css";

type CompareShellProps = Readonly<{ items?: readonly CompareItem[]; onRemove?: (id: string) => void; onClear?: () => void }>;
const categoryTabs: ReadonlyArray<{ id: CompareCategory; label: string }> = [
  { id: "all", label: "All options" }, { id: "property", label: "Properties" }, { id: "project", label: "Projects" }, { id: "locality", label: "Locations" },
];

export default function CompareShell({ items = [], onRemove, onClear }: CompareShellProps) {
  const [category, setCategory] = useState<CompareCategory>("all");
  const [selectedGroups, setSelectedGroups] = useState<CompareFieldGroup[]>(COMPARE_FIELD_GROUPS.map((group) => group.id));
  const visibleItems = useMemo(() => items.filter((item) => category === "all" || item.kind === category).slice(0, COMPARE_MAX_ITEMS), [items, category]);
  const overflow = items.length > COMPARE_MAX_ITEMS;
  function changeGroup(group: CompareFieldGroup, selected: boolean) {
    setSelectedGroups((current) => selected ? Array.from(new Set([...current, group])) : current.filter((item) => item !== group));
  }

  return <main className={styles.experience}><div className={styles.ambient} aria-hidden="true" /><div className={styles.inner}>
    <header className={styles.hero}><div><p className={styles.eyebrow}><span className={styles.eyebrowDot} /> DECISION STUDIO</p><h1>Clarity, <em>side by side.</em></h1><p className={styles.heroText}>Compare what matters—not just a list of fields. Keep the differences clear, the missing facts honest, and the next step within reach.</p></div><div className={styles.heroMetric}><span className={styles.metricLabel}>OPTIONS IN VIEW</span><strong>{String(visibleItems.length).padStart(2, "0")}</strong><span className={styles.metricFoot}>up to {COMPARE_MAX_ITEMS} at once</span></div></header>
    <section className={styles.workspace} aria-label="Compare options"><div className={styles.workspaceHead}><div><p className={styles.eyebrow}>SIDE-BY-SIDE VIEW</p><h2>Make the differences visible.</h2></div><span className={styles.secureNote}><span className={styles.syncPulse} aria-hidden="true" /> Source-supplied facts only</span></div>
      {items.length === 0 ? <CompareEmptyState /> : <>
        {overflow ? <p className={styles.infoNotice} role="status">Showing the first {COMPARE_MAX_ITEMS} items to keep this comparison readable. Narrow the set in the connected shortlist controls to compare other options.</p> : null}
        <CompareSummary items={visibleItems} />
        <div className={styles.tabs} role="tablist" aria-label="Filter comparison by option type">{categoryTabs.map((tab) => <button key={tab.id} type="button" role="tab" aria-selected={category === tab.id} className={`${styles.tab} ${category === tab.id ? styles.activeTab : ""}`} onClick={() => setCategory(tab.id)}>{tab.label}<span>{tab.id === "all" ? items.length : items.filter((item) => item.kind === tab.id).length}</span></button>)}</div>
        <CompareCriteria selected={selectedGroups} onChange={changeGroup} />
        <div className={styles.comparePanel}>
          {category === "all" ? <CompareTable items={visibleItems} selectedGroups={selectedGroups} onRemove={onRemove} /> : null}
          {category === "property" ? <CompareProperties items={visibleItems} selectedGroups={selectedGroups} onRemove={onRemove} /> : null}
          {category === "project" ? <CompareProjects items={visibleItems} selectedGroups={selectedGroups} onRemove={onRemove} /> : null}
          {category === "locality" ? <CompareLocalities items={visibleItems} selectedGroups={selectedGroups} onRemove={onRemove} /> : null}
        </div>
        <CompareActions items={visibleItems} onClear={onClear} />
      </>}
    </section>
  </div></main>;
}
