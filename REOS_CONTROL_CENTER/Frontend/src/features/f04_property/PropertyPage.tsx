import Link from "next/link";

import PropertyActionBar from "./PropertyActionBar";
import PropertyAI from "./PropertyAI";
import PropertyAmenities from "./PropertyAmenities";
import PropertyDetails from "./PropertyDetails";
import PropertyDisclosure from "./PropertyDisclosure";
import PropertyFacts from "./PropertyFacts";
import PropertyGallery from "./PropertyGallery";
import PropertyLocation from "./PropertyLocation";
import PropertyNextStep from "./PropertyNextStep";
import PropertyProjectContext from "./PropertyProjectContext";
import PropertySummary from "./PropertySummary";
import PropertyTrust from "./PropertyTrust";
import SimilarProperties from "./SimilarProperties";
import type { PropertyRecord } from "./property.types";

import styles from "./PropertyPage.module.css";

type PropertyPageProps = Readonly<{
  property: PropertyRecord;
}>;

type DiscoveryIntent = "buy" | "projects";

function buildSearchHref(
  property: PropertyRecord,
  intent: DiscoveryIntent,
  includeLocality = false,
): string {
  const params = new URLSearchParams();

  params.set("intent", intent);

  if (property.city.trim()) {
    params.set("city", property.city.trim());
  }

  if (property.country.trim()) {
    params.set("country", property.country.trim());
  }

  if (includeLocality && property.locality.trim()) {
    params.set("locality", property.locality.trim());
  }

  return `/search?${params.toString()}`;
}

export default function PropertyPage({ property }: PropertyPageProps) {
  const citySearchHref = buildSearchHref(property, "buy");
  const localitySearchHref = buildSearchHref(property, "buy", true);
  const projectSearchHref = buildSearchHref(property, "projects");

  return (
    <main className={styles.page}>
      <div className="homio-container">
        <nav className={styles.breadcrumbs} aria-label="Breadcrumb">
          <Link href="/">HOMIO</Link>
          <span aria-hidden="true">›</span>
          <Link href="/search">Search</Link>
          <span aria-hidden="true">›</span>
          <span aria-current="page">{property.shortTitle}</span>
        </nav>

        <div className={styles.topGrid}>
          <PropertyGallery key={property.id} media={property.media} />

          <aside className={styles.summaryColumn}>
            <PropertySummary property={property} />
            <PropertyActionBar property={property} />
          </aside>
        </div>

        <PropertyFacts property={property} />
        <PropertyDetails property={property} />
        <PropertyProjectContext property={property} />
        <PropertyAmenities property={property} />
        <PropertyLocation property={property} />
        <PropertyTrust property={property} />

        <PropertyDisclosure
          verified={property.verified}
          verificationLabel={property.verificationLabel}
        />

        <PropertyAI />
        <SimilarProperties property={property} />

        <PropertyNextStep property={property} />

        <section className={styles.related}>
          <div className={styles.relatedHeader}>
            <span className={styles.eyebrow}>CONTINUE DISCOVERY</span>
            <h2>Explore more around this property.</h2>
          </div>

          <div className={styles.relatedGrid}>
            <Link href={citySearchHref} className={styles.relatedCard}>
              <strong>Explore {property.city} property previews</strong>
              <span>Discover more opportunities in this city</span>
            </Link>

            <Link href={localitySearchHref} className={styles.relatedCard}>
              <strong>Explore {property.locality}</strong>
              <span>Continue discovery in this locality</span>
            </Link>

            <Link href={projectSearchHref} className={styles.relatedCard}>
              <strong>Explore projects in {property.city}</strong>
              <span>Browse project and collection previews</span>
            </Link>
          </div>
        </section>
      </div>
    </main>
  );
}
