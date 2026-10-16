"use client";

import styles from "./PostProperty.module.css";
import type { PropertyDetails } from "./post-property.types";

type Props = Readonly<{
  value: PropertyDetails;
  onChange: (next: PropertyDetails) => void;
  disabled?: boolean;
}>;

export default function PostPropertyDetails({ value, onChange, disabled = false }: Props) {
  function update<K extends keyof PropertyDetails>(key: K, next: PropertyDetails[K]) {
    onChange({ ...value, [key]: next });
  }

  return (
    <section className={styles.postPanel}>
      <header className={styles.postPanelHeader}>
        <h2 className={styles.postPanelTitle}>Property details</h2>
        <p className={styles.postPanelDescription}>Enter information supplied by the authorized property source. Values are not independently verified at this stage.</p>
      </header>

      <div className={styles.postFieldGrid}>
        <div className={`${styles.postField} ${styles.postFieldFull}`}>
          <label className={styles.postLabel} htmlFor="property-title">Listing title</label>
          <input id="property-title" className={styles.postInput} value={value.title} maxLength={160} disabled={disabled} onChange={(event) => update("title", event.currentTarget.value)} />
        </div>

        <div className={styles.postField}>
          <label className={styles.postLabel} htmlFor="property-type">Property type</label>
          <input id="property-type" className={styles.postInput} value={value.propertyType} maxLength={80} disabled={disabled} onChange={(event) => update("propertyType", event.currentTarget.value)} placeholder="Apartment, house, office…" />
        </div>

        <div className={styles.postField}>
          <label className={styles.postLabel} htmlFor="property-area">Area</label>
          <input id="property-area" className={styles.postInput} type="number" min="0" step="any" value={value.area} disabled={disabled} onChange={(event) => update("area", event.currentTarget.value)} />
        </div>

        <div className={styles.postField}>
          <label className={styles.postLabel} htmlFor="property-bedrooms">Bedrooms</label>
          <input id="property-bedrooms" className={styles.postInput} type="number" min="0" max="100" step="1" value={value.bedrooms} disabled={disabled} onChange={(event) => update("bedrooms", event.currentTarget.value)} />
        </div>

        <div className={styles.postField}>
          <label className={styles.postLabel} htmlFor="property-bathrooms">Bathrooms</label>
          <input id="property-bathrooms" className={styles.postInput} type="number" min="0" max="100" step="1" value={value.bathrooms} disabled={disabled} onChange={(event) => update("bathrooms", event.currentTarget.value)} />
        </div>

        <div className={`${styles.postField} ${styles.postFieldFull}`}>
          <label className={styles.postLabel} htmlFor="property-description">Description</label>
          <textarea id="property-description" className={styles.postTextarea} value={value.description} maxLength={5000} disabled={disabled} onChange={(event) => update("description", event.currentTarget.value)} />
          <span className={styles.postHint}>{value.description.length}/5000 characters</span>
        </div>
      </div>
    </section>
  );
}
