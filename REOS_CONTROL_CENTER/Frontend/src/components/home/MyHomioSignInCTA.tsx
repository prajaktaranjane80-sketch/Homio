import Link from "next/link";
import styles from "./MyHomioSignInCTA.module.css";

export default function MyHomioSignInCTA() {
  return (
    <div className={styles.wrapper}>
      <div>
        <strong>Pick up where you left off.</strong>

        <p>
          Sign in to keep your discovery and brokerage journey connected across
          devices.
        </p>
      </div>

      <Link href="/my">Continue to My HOMIO</Link>
    </div>
  );
}
