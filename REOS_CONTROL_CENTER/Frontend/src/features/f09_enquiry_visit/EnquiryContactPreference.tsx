"use client";

import type { ContactPreference } from "./enquiry.types";

import { CONTACT_PREFERENCE_OPTIONS } from "./enquiry.constants";
import styles from "./EnquiryWorkspace.module.css";

type Props = Readonly<{
  value: ContactPreference;
  onChange: (value: ContactPreference) => void;
  idPrefix?: string;
  disabled?: boolean;
  error?: string;
}>;

export default function EnquiryContactPreference({
  value,
  onChange,
  idPrefix = "enquiry-contact",
  disabled = false,
  error,
}: Props) {
  const errorId = `${idPrefix}-error`;

  return (
    <fieldset
      className={styles.field}
      aria-describedby={error ? errorId : undefined}
    >
      <legend className={styles.label}>
        Preferred contact method
      </legend>

      <div className={styles.choiceGroup}>
        {CONTACT_PREFERENCE_OPTIONS.map((option) => {
          const id = `${idPrefix}-${option.value}`;

          return (
            <label className={styles.choice} htmlFor={id} key={option.value}>
              <input
                id={id}
                name={`${idPrefix}-preference`}
                type="radio"
                value={option.value}
                checked={value === option.value}
                disabled={disabled}
                onChange={() => onChange(option.value)}
              />

              <span className={styles.choiceCopy}>
                <span className={styles.choiceTitle}>
                  {option.label}
                </span>

                <span className={styles.choiceDescription}>
                  Use this channel for this property-related request.
                </span>
              </span>
            </label>
          );
        })}
      </div>

      <p className={styles.fieldHelp}>
        Contact preference is not consent by itself. The form asks for contact consent separately.
      </p>

      {error ? (
        <p className={styles.fieldError} id={errorId} role="alert">
          {error}
        </p>
      ) : null}
    </fieldset>
  );
}
