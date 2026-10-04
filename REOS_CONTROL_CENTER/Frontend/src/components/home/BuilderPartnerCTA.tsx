import Link from "next/link";
import styles from "./BuilderPartnerCTA.module.css";

export default function BuilderPartnerCTA() {
  return (
    <div className={styles.wrapper}>
      <div>
        <span>FOR BUILDERS & DEVELOPERS</span>

        <strong>
          Bring your project inventory into a structured HOMIO discovery and
          brokerage journey.
        </strong>
      </div>

      <Link href="/pro/inventory">
        Explore partner pathway
      </Link>
    </div>
  );
}
