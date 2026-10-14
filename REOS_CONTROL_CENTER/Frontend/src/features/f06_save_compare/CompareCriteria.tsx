import { COMPARE_FIELD_GROUPS, type CompareFieldGroup } from "./compare.types";
import styles from "./SavedCompareExperience.module.css";

type CompareCriteriaProps = Readonly<{ selected: readonly CompareFieldGroup[]; onChange: (group: CompareFieldGroup, selected: boolean) => void }>;

export default function CompareCriteria({ selected, onChange }: CompareCriteriaProps) {
  return <fieldset className={styles.criteria}><legend>What matters to you?</legend><p className={styles.criteriaIntro}>Choose the details that help you decide. Only facts supplied by the source will be shown.</p><div className={styles.criteriaOptions}>{COMPARE_FIELD_GROUPS.map((group) => <label className={styles.criteriaOption} key={group.id}><input type="checkbox" checked={selected.includes(group.id)} onChange={(event) => onChange(group.id, event.target.checked)} /><span className={styles.fakeCheck} aria-hidden="true">✓</span><span><strong>{group.label}</strong><small>{group.description}</small></span></label>)}</div></fieldset>;
}
