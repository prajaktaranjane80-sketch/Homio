"use client";

import type {
  ContactPreference,
  EnquiryValidationErrors,
} from "./enquiry.types";

import styles from "./EnquiryWorkspace.module.css";

type ContactField = "fullName" | "email" | "phone";

type Props = Readonly<{
  fullName: string;
  email: string;
  phone: string;
  preference: ContactPreference;
  idPrefix: string;
  errors: EnquiryValidationErrors;
  onChange: (field: ContactField, value: string) => void;
}>;

export default function EnquiryContactDetails({
  fullName,
  email,
  phone,
  preference,
  idPrefix,
  errors,
  onChange,
}: Props) {
  const nameId = `${idPrefix}-name`;
  const emailId = `${idPrefix}-email`;
  const phoneId = `${idPrefix}-phone`;

  return (
    <section className={styles.stack} aria-labelledby={`${idPrefix}-heading`}>
      <div>
        <p className={styles.kicker}>CONTACT DETAILS</p>
        <h3 className={styles.statusTitle} id={`${idPrefix}-heading`}>
          How should HOMIO reach you?
        </h3>
        <p className={styles.fieldHelp}>
          Provide only the contact details needed for your request.
        </p>
      </div>

      <div className={styles.field}>
        <label className={styles.label} htmlFor={nameId}>
          Full name
        </label>
        <input
          className={styles.input}
          id={nameId}
          name="fullName"
          autoComplete="name"
          value={fullName}
          maxLength={120}
          required
          aria-invalid={Boolean(errors.fullName)}
          aria-describedby={errors.fullName ? `${nameId}-error` : undefined}
          onChange={(event) => onChange("fullName", event.currentTarget.value)}
          placeholder="Your full name"
        />
        {errors.fullName ? (
          <p className={styles.fieldError} id={`${nameId}-error`} role="alert">
            {errors.fullName}
          </p>
        ) : null}
      </div>

      <div className={styles.field}>
        <label className={styles.label} htmlFor={emailId}>
          Email address
          {preference === "email" ? null : (
            <span className={styles.optional}>Optional</span>
          )}
        </label>
        <input
          className={styles.input}
          id={emailId}
          name="email"
          type="email"
          autoComplete="email"
          inputMode="email"
          maxLength={254}
          value={email}
          required={preference === "email"}
          aria-invalid={Boolean(errors.email)}
          aria-describedby={errors.email ? `${emailId}-error` : undefined}
          onChange={(event) => onChange("email", event.currentTarget.value)}
          placeholder="you@example.com"
        />
        {errors.email ? (
          <p className={styles.fieldError} id={`${emailId}-error`} role="alert">
            {errors.email}
          </p>
        ) : null}
      </div>

      <div className={styles.field}>
        <label className={styles.label} htmlFor={phoneId}>
          Phone number
          {preference === "email" ? (
            <span className={styles.optional}>Optional</span>
          ) : null}
        </label>
        <input
          className={styles.input}
          id={phoneId}
          name="phone"
          type="tel"
          autoComplete="tel"
          inputMode="tel"
          maxLength={32}
          value={phone}
          required={preference !== "email"}
          aria-invalid={Boolean(errors.phone)}
          aria-describedby={errors.phone ? `${phoneId}-error` : undefined}
          onChange={(event) => onChange("phone", event.currentTarget.value)}
          placeholder="Include country calling code"
        />
        {errors.phone ? (
          <p className={styles.fieldError} id={`${phoneId}-error`} role="alert">
            {errors.phone}
          </p>
        ) : null}
        <p className={styles.fieldHelp}>
          Use an international format when possible, for example +971 or +65.
        </p>
      </div>
    </section>
  );
}
