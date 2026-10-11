import styles from "./WhyHomioStatement.module.css";

export default function WhyHomioStatement() {
  return (
    <div className={styles.statement}>
      <span className={styles.quoteMark}>“</span>

      <div>
        <p>
          From finding a property to completing a transaction, every step
          should feel like part of the same journey.
        </p>

        <span>The HOMIO experience principle</span>
      </div>
    </div>
  );
}
