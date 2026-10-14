import type { CompareItem } from "./compare.types";
import ShareComparison from "./ShareComparison";
import styles from "./SavedCompareExperience.module.css";

type CompareActionsProps = Readonly<{ items: readonly CompareItem[]; onClear?: () => void }>;

export default function CompareActions({ items, onClear }: CompareActionsProps) {
  return <div className={styles.compareActions}><div><p className={styles.eyebrow}>NEXT STEP</p><strong>Ready to keep exploring?</strong><span>Open an option for its available details, or share this comparison context.</span></div><div className={styles.actionCluster}><ShareComparison ids={items.map((item) => item.id)} disabled={items.length < 2} />{onClear ? <button type="button" className={styles.secondaryAction} onClick={onClear}>Clear comparison</button> : null}</div></div>;
}
