"use client";

import styles from "./PostProperty.module.css";
import type { PropertyOwnership } from "./post-property.types";

type Props = Readonly<{
  value: PropertyOwnership | "";
  onChange: (value: PropertyOwnership) => void;
  disabled?: boolean;
}>;

const OPTIONS: readonly Readonly<{
  value: PropertyOwnership;
  title: string;
  description: string;
}>[] = [
  { value: "owner", title: "Property owner", description: "You own the property being submitted." },
  { value: "authorized_agent", title: "Authorized agent", description: "You have permission to represent the owner." },
  { value: "developer", title: "Developer / builder", description: "You represent the relevant development entity." },
  { value: "authorized_partner", title: "Authorized partner", description: "You act for an approved inventory partner." },
];

export default function PostPropertyOwnership({ value, onChange, disabled = false }: Props) {
  return (
    <section className={styles.postPanel}>
      <header className={styles.postPanelHeader}>
        <h2 className={styles.postPanelTitle}>Your relationship to the property</h2>
        <p className={styles.postPanelDescription}>This self-selected answer is not proof of ownership or authority.</p>
      </header>

      <div className={styles.postChoiceGrid}>
        {OPTIONS.map((option) => (
          <label className={styles.postChoice} key={option.value}>
            <input
              type="radio"
              name="post-property-ownership"
              value={option.value}
              checked={value === option.value}
              disabled={disabled}
              onChange={() => onChange(option.value)}
            />
            <span className={styles.postChoiceText}>
              <span className={styles.postChoiceTitle}>{option.title}</span>
              <span className={styles.postChoiceDescription}>{option.description}</span>
            </span>
          </label>
        ))}
      </div>

      <p className={styles.postNotice}>
        Ownership and representative authority require the applicable verification process before a listing can be approved.
      </p>
    </section>
  );
}
