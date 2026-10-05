"use client";

import styles from "./SearchVerificationFilter.module.css";

type SearchVerificationFilterProps = Readonly<{
  value: boolean;
  onChange: (value: boolean) => void;
}>;

export default function SearchVerificationFilter({
  value,
  onChange,
}: SearchVerificationFilterProps) {
  return (
    <fieldset className={styles.fieldset}>
      <legend>Trust & verification</legend>

      <button
        type="button"
        role="switch"
        aria-checked={value}
        className={`${styles.control} ${value ? styles.active : ""}`}
        onClick={() => onChange(!value)}
      >
        <span className={styles.switch} aria-hidden="true">
          <span className={styles.knob} />
        </span>

        <span className={styles.content}>
          <strong>HOMIO Verified only</strong>

          <span>
            Show inventory carrying the strongest available HOMIO verification
            signals.
          </span>
        </span>
      </button>
    </fieldset>
  );
}
