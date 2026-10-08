import styles from "./loading.module.css";

export default function ProjectLoading() {
  return (
    <main className={styles.page}>
      <div className="homio-container">
        <div className={styles.breadcrumb} />

        <div className={styles.hero}>
          <section className={styles.gallery} />

          <section className={styles.summary}>
            <div className={styles.lineSmall} />
            <div className={styles.lineLarge} />
            <div className={styles.lineMedium} />

            <div className={styles.facts}>
              <span />
              <span />
              <span />
              <span />
            </div>

            <div className={styles.actions}>
              <span />
              <span />
              <span />
            </div>
          </section>
        </div>

        <div className={styles.content} />
        <div className={styles.contentShort} />
      </div>
    </main>
  );
}
