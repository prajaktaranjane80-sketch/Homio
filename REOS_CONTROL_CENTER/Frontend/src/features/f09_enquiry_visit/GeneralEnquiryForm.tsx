"use client";

import { useState, type FormEvent } from "react";

import type {
  ContactPreference,
  EnquiryDraft,
  EnquiryPurpose,
  EnquiryQualification as QualificationValue,
  EnquiryTarget,
  EnquiryTimeframe,
  EnquiryValidationErrors,
} from "./enquiry.types";

import {
  ENQUIRY_PURPOSE_OPTIONS,
  ENQUIRY_SERVICE_NOTICE,
  isValidEmail,
  isValidInternationalPhone,
} from "./enquiry.constants";

import EnquiryContactDetails from "./EnquiryContactDetails";
import EnquiryContactPreference from "./EnquiryContactPreference";
import EnquiryQualification from "./EnquiryQualification";

import styles from "./EnquiryWorkspace.module.css";

type FormValues = Omit<EnquiryDraft, "target">;

type Props = Readonly<{
  onDraftReady?: (draft: EnquiryDraft) => void;
}>;

const GENERAL_TARGET: EnquiryTarget = {
  kind: "general",
  title: "General HOMIO enquiry",
};

function createInitialValues(): FormValues {
  return {
    purpose: "general",
    fullName: "",
    email: "",
    phone: "",
    contactPreference: "email",
    qualification: "researching",
    timeframe: "flexible",
    budgetAmount: "",
    budgetCurrency: "INR",
    message: "",
    consentToContact: false,
    consentToMarketing: false,
  };
}

export default function GeneralEnquiryForm({
  onDraftReady,
}: Props) {
  const [form, setForm] = useState<FormValues>(createInitialValues);
  const [errors, setErrors] = useState<EnquiryValidationErrors>({});
  const [draftReady, setDraftReady] = useState(false);

  function update<K extends keyof FormValues>(
    key: K,
    value: FormValues[K],
  ) {
    setForm((current) => ({ ...current, [key]: value }));
    setDraftReady(false);
    setErrors((current) => ({ ...current, [key]: undefined }));
  }

  function updateContact(
    field: "fullName" | "email" | "phone",
    value: string,
  ) {
    setForm((current) => ({ ...current, [field]: value }));
    setDraftReady(false);
    setErrors((current) => ({ ...current, [field]: undefined }));
  }

  function validate(): EnquiryValidationErrors {
    const next: EnquiryValidationErrors = {};

    if (!form.fullName.trim()) {
      next.fullName = "Enter your name.";
    }

    if (
      form.email.trim() &&
      !isValidEmail(form.email)
    ) {
      next.email = "Enter a valid email address.";
    } else if (
      form.contactPreference === "email" &&
      !isValidEmail(form.email)
    ) {
      next.email = "An email address is required for your chosen contact method.";
    }

    if (
      form.phone.trim() &&
      !isValidInternationalPhone(form.phone)
    ) {
      next.phone = "Enter a valid international phone number.";
    } else if (
      form.contactPreference !== "email" &&
      !isValidInternationalPhone(form.phone)
    ) {
      next.phone = "A valid phone number is required for your chosen contact method.";
    }

    if (!form.message.trim()) {
      next.message = "Describe your question so it can be reviewed.";
    }

    if (!form.consentToContact) {
      next.consentToContact =
        "Confirm contact consent before preparing this enquiry draft.";
    }

    return next;
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const nextErrors = validate();
    setErrors(nextErrors);

    if (Object.values(nextErrors).some(Boolean)) {
      setDraftReady(false);
      return;
    }

    const draft: EnquiryDraft = {
      ...form,
      target: GENERAL_TARGET,
    };

    onDraftReady?.(draft);
    setDraftReady(true);
  }

  return (
    <section className={styles.panel} aria-labelledby="general-enquiry-title">
      <header className={styles.panelHeader}>
        <div className={styles.panelHeaderMain}>
          <p className={styles.kicker}>GENERAL ENQUIRY</p>
          <h2 className={styles.panelTitle} id="general-enquiry-title">
            What can we help you with?
          </h2>
          <p className={styles.panelLead}>
            Share a property-related question, a broader requirement or feedback about the HOMIO experience.
          </p>
        </div>

        <span className={styles.badge}>General request</span>
      </header>

      <div className={styles.notice} role="note">
        <strong>Preview mode — nothing will be sent</strong>
        <p>{ENQUIRY_SERVICE_NOTICE}</p>
      </div>

      <form className={styles.form} onSubmit={handleSubmit} noValidate>
        <div className={styles.field}>
          <label className={styles.label} htmlFor="general-enquiry-purpose">
            Enquiry category
          </label>
          <select
            className={styles.select}
            id="general-enquiry-purpose"
            value={form.purpose}
            onChange={(event) =>
              update("purpose", event.currentTarget.value as EnquiryPurpose)
            }
          >
            {ENQUIRY_PURPOSE_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <EnquiryQualification
          qualification={form.qualification}
          timeframe={form.timeframe}
          onQualificationChange={(value: QualificationValue) =>
            update("qualification", value)
          }
          onTimeframeChange={(value: EnquiryTimeframe) =>
            update("timeframe", value)
          }
        />

        <EnquiryContactDetails
          idPrefix="general-enquiry"
          fullName={form.fullName}
          email={form.email}
          phone={form.phone}
          preference={form.contactPreference}
          errors={errors}
          onChange={updateContact}
        />

        <EnquiryContactPreference
          idPrefix="general-enquiry-contact"
          value={form.contactPreference}
          onChange={(value: ContactPreference) =>
            update("contactPreference", value)
          }
        />

        <div className={styles.field}>
          <label className={styles.label} htmlFor="general-enquiry-message">
            Your question or requirement
          </label>
          <textarea
            className={styles.textarea}
            id="general-enquiry-message"
            rows={5}
            maxLength={2000}
            value={form.message}
            aria-invalid={Boolean(errors.message)}
            aria-describedby={errors.message ? "general-enquiry-message-error" : undefined}
            onChange={(event) => update("message", event.currentTarget.value)}
            placeholder="Describe your question, the type of help you need and any useful context."
          />
          {errors.message ? (
            <p
              className={styles.fieldError}
              id="general-enquiry-message-error"
              role="alert"
            >
              {errors.message}
            </p>
          ) : null}
          <p className={styles.fieldHelp}>
            Do not include passwords, payment details or sensitive identity documents.
          </p>
        </div>

        <div className={styles.consentBlock}>
          <label className={styles.consentLine}>
            <input
              type="checkbox"
              checked={form.consentToContact}
              aria-invalid={Boolean(errors.consentToContact)}
              onChange={(event) =>
                update("consentToContact", event.currentTarget.checked)
              }
            />
            <span>
              I consent to being contacted about this enquiry if an authorised enquiry service is connected and the request is submitted.
            </span>
          </label>

          {errors.consentToContact ? (
            <p className={styles.fieldError} role="alert">
              {errors.consentToContact}
            </p>
          ) : null}

          <label className={styles.consentLine}>
            <input
              type="checkbox"
              checked={form.consentToMarketing}
              onChange={(event) =>
                update("consentToMarketing", event.currentTarget.checked)
              }
            />
            <span>
              I would also like to receive optional HOMIO property updates.
            </span>
          </label>
        </div>

        <p className={styles.privacyNote}>
          Details remain in this component&apos;s page state in the current preview. They are not sent to a service or saved in browser storage.
        </p>

        <div className={styles.formActions}>
          <button className={styles.primaryButton} type="submit">
            Review enquiry draft <span aria-hidden="true">↗</span>
          </button>
        </div>
      </form>

      {draftReady ? (
        <div className={styles.successBanner} role="status" aria-live="polite">
          <strong>General enquiry draft prepared</strong>
          <p>
            This draft is ready for review in this page only. Nothing was submitted and no enquiry reference was generated.
          </p>
        </div>
      ) : null}
    </section>
  );
}
