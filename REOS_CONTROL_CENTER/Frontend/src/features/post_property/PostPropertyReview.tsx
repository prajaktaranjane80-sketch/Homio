import styles from "./PostProperty.module.css";
import type { PostPropertyDraft } from "./post-property.types";

type Props = Readonly<{
  draft: PostPropertyDraft;
}>;

function ReviewItem({ label, value }: Readonly<{ label: string; value?: string }>) {
  return (
    <div className={styles.postReviewItem}>
      <span className={styles.postReviewLabel}>{label}</span>
      <span className={styles.postReviewValue}>{value?.trim() || "Not provided"}</span>
    </div>
  );
}

export default function PostPropertyReview({ draft }: Props) {
  const details = draft.details;

  return (
    <section className={styles.postPanel}>
      <header className={styles.postPanelHeader}>
        <h2 className={styles.postPanelTitle}>Review your draft</h2>
        <p className={styles.postPanelDescription}>Check the information supplied before requesting submission.</p>
      </header>

      <div className={styles.postReviewGrid}>
        <ReviewItem label="Listing intent" value={draft.listingIntent} />
        <ReviewItem label="Market" value={draft.marketId} />
        <ReviewItem label="Country" value={draft.countryCode} />
        <ReviewItem label="Locality" value={draft.locality} />
        <ReviewItem label="Ownership relationship" value={draft.ownership} />
        <ReviewItem label="Property type" value={details?.propertyType} />
        <ReviewItem label="Title" value={details?.title} />
        <ReviewItem label="Area" value={details?.area ? `${details.area} ${details.areaUnit}` : undefined} />
        <ReviewItem label="Bedrooms" value={details?.bedrooms} />
        <ReviewItem label="Bathrooms" value={details?.bathrooms} />
        <ReviewItem label="Asking price" value={draft.askingPrice ? `${draft.askingPrice} ${draft.currency ?? ""}`.trim() : undefined} />
        <ReviewItem label="Availability (submitter stated)" value={draft.availability} />
        <ReviewItem label="Selected media files" value={String(draft.mediaFileNames?.length ?? 0)} />
        <ReviewItem label="Selected document files" value={String(draft.documentFileNames?.length ?? 0)} />
      </div>

      <div className={styles.postField}>
        <span className={styles.postLabel}>Description</span>
        <p className={styles.postDescription}>{details?.description?.trim() || "No description provided."}</p>
      </div>

      <p className={styles.postNotice}>
        Review confirms only what is in this draft. It does not establish ownership, document validity, availability or listing approval.
      </p>
    </section>
  );
}
