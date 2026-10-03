import Link from "next/link";
import styles from "./HomeHeader.module.css";

export default function HomeHeader() {
  return (
    <header className={styles.header}>
      <div className={`homio-container ${styles.inner}`}>
        <Link href="/" className={styles.logo} aria-label="HOMIO home">
          <span className={styles.logoMark}>H</span>
          <span className={styles.logoText}>HOMIO</span>
        </Link>

        <nav className={styles.navigation} aria-label="Primary navigation">
          <Link href="/search?intent=buy">Buy</Link>
          <Link href="/search?intent=rent">Rent</Link>
          <Link href="/search?intent=commercial">Commercial</Link>
          <Link href="/project/featured">Projects</Link>
        </nav>

        <div className={styles.actions}>
          <Link href="/saved" className={styles.actionLink}>
            Saved
          </Link>
          <Link href="/my" className={styles.accountButton}>
            My HOMIO
          </Link>
        </div>
      </div>
    </header>
  );
}
