import Link from "next/link";
import PropertyActionBar from "./PropertyActionBar";
import PropertyAmenities from "./PropertyAmenities";
import PropertyDetails from "./PropertyDetails";
import PropertyGallery from "./PropertyGallery";
import PropertyLocation from "./PropertyLocation";
import PropertySummary from "./PropertySummary";
import PropertyTrust from "./PropertyTrust";
import type { PropertyRecord } from "./property.types";
import styles from "./PropertyPage.module.css";

type PropertyPageProps = Readonly<{
  property: PropertyRecord;
}>;

export default function PropertyPage({
  property,
}: PropertyPageProps) {
  return (
    <main className={styles.page}>
      <div className="homio-container">
        <nav className={styles.breadcrumbs} aria-label="Breadcrumb">
          <Link href="/">HOMIO</Link>
          <span>›</span>
          <Link href="/search">Search</Link>
          <span>›</span>
          <span>{property.shortTitle}</span>
        </nav>

        <div className={styles.topGrid}>
          <PropertyGallery media={property.media} />

          <aside className={styles.summaryColumn}>
            <PropertySummary property={property} />
            <PropertyActionBar />
          </aside>
        </div>

        <PropertyDetails property={property} />
        <PropertyAmenities property={property} />
        <PropertyLocation property={property} />
        <PropertyTrust property={property} />

        <section className={styles.ai}>
          <span className={styles.eyebrow}>HOMIO AI</span>
          <h2>Need help deciding what matters?</h2>
          <p>
            Ask HOMIO to explain the property, compare it with another
            option or help you understand the next step.
          </p>
          <button type="button">Ask HOMIO</button>
        </section>

        <section className={styles.related}>
          <div>
            <span className={styles.eyebrow}>CONTINUE DISCOVERY</span>
            <h2>Explore more around this property.</h2>
          </div>

          <div className={styles.relatedGrid}>
            <Link href="/search?city=Pune" className={styles.relatedCard}>
              <strong>More Pune properties</strong>
              <span>Continue property discovery</span>
            </Link>

            <Link
              href="/search?locality=Kalyani%20Nagar"
              className={styles.relatedCard}
            >
              <strong>Explore Kalyani Nagar</strong>
              <span>See locality opportunities</span>
            </Link>

            <Link href="/search?intent=projects" className={styles.relatedCard}>
              <strong>View projects</strong>
              <span>Explore project-led discovery</span>
            </Link>
          </div>
        </section>
      </div>
    </main>
  );
}
