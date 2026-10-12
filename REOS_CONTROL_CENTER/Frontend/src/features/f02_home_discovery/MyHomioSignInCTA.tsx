import styles from "./MyHomioSignInCTA.module.css";

export default function MyHomioSignInCTA() {
  return (
    <div className={styles.wrapper}>
      <div>
        <strong>Pick up where you left off.</strong>

        <p>
          Persistent account access is planned for the My HOMIO journey.
          Sign-in and synchronisation are not enabled in this preview.
        </p>
      </div>

      <span className={styles.status} aria-disabled="true">
        Sign-in not active
      </span>
    </div>
  );
}
