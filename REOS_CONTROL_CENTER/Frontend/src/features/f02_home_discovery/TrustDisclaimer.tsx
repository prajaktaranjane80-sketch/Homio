import Link from "next/link";
import styles from "./TrustDisclaimer.module.css";

export default function TrustDisclaimer() {
  return (
    <div className={styles.wrapper}>
      <span>
        <strong>Important:</strong> trust signals support informed decisions;
        they do not replace independent due diligence.
      </span>

      <Link href="/">Back to top</Link>
    </div>
  );
}
