import Link from "next/link";
import styles from "./SaveCompareCTA.module.css";

export default function SaveCompareCTA() {
  return (
    <div className={styles.wrapper}>
      <div>
        <span>YOUR JOURNEY</span>
        <strong>Save now. Compare later. Continue where you left off.</strong>
      </div>

      <Link href="/my">Open My HOMIO</Link>
    </div>
  );
}
