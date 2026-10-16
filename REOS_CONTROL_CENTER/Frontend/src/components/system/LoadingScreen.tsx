
/* File: src/components/system/LoadingScreen.tsx */
import styles from "./SharedSystem.module.css";

type Props = Readonly<{
  label?: string;
  description?: string;
}>;

export default function LoadingScreen({
  label = "Loading workspace",
  description = "Preparing the requested view.",
}: Props) {
  return (
    <section className={styles.systemLoading} role="status" aria-live="polite">
      <span className={styles.loadingSpinner} aria-hidden="true" />
      <p className={styles.loadingTitle}>{label}</p>
      <p className={styles.loadingDescription}>{description}</p>
    </section>
  );
}
