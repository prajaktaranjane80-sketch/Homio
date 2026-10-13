import Link from "next/link";

import styles from "./MyHomioSignInCTA.module.css";

export default function MyHomioSignInCTA() {
  return (
    <div className={styles.wrapper}>
      <div>
        <strong>Your property journey, connected to your account.</strong>
        <p>
          Sign in to open My HOMIO. Saved properties and searches will sync here
          when their authorized persistence services are connected.
        </p>
      </div>
      <div className={styles.actions}>
        <Link href="/login">Sign in</Link>
        <Link className={styles.secondary} href="/signup">Create account</Link>
      </div>
    </div>
  );
}