import Link from "next/link";
import styles from "./FooterLegal.module.css";

export default function FooterLegal() {
  return (
    <div className={styles.wrapper}>
      <span>© 2026 HOMIO. Global real estate experience.</span>

      <div className={styles.links}>
        <Link href="/search">Property search</Link>
        <Link href="/">Home</Link>
      </div>
    </div>
  );
}
