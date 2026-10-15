"use client";

import { useState, type FormEvent } from "react";

import type {
  ContactPreference,
  EnquiryDraft,
  EnquiryPurpose,
  EnquiryQualification as QualificationValue,
  EnquiryTimeframe,
  EnquiryValidationErrors,
} from "./enquiry.types";

import {
  ENQUIRY_CURRENCY_OPTIONS,
  ENQUIRY_PURPOSE_OPTIONS,
  ENQUIRY_SERVICE_NOTICE,
  isValidEmail,
  isValidInternationalPhone,
} from "./enquiry.constants";

import EnquiryContactDetails from "./EnquiryContactDetails";
import EnquiryContactPreference from "./EnquiryContactPreference";
import EnquiryQualification from "./EnquiryQualification";

import styles from "./EnquiryWorkspace.module.css";

type ProjectTarget = Readonly<{
  kind: "project";
  id: string;
  title: string;
  location?: string;
  href?: string;
}>;

type FormValues = Omit<EnquiryDraft, "target">;

type Props = Readonly<{
  target: ProjectTarget;
  onDraftReady?: (draft: EnquiryDraft) => void;
}>;

function createInitialValues(): FormValues {
  return {
    purpose: "invest",
    fullName: "",
    email: "",
    phone: "",
    contactPreference: "email",
    qualification: "exploring",
    timeframe: "flexible",
    budgetAmount: "",
    budgetCurrency: "INR",
    message: "",
    consentToContact: false,
    consentToMarketing: false,
  };
}

export default function ProjectEnquiryForm({
  target,
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

    if (
      form.budgetAmount.trim() &&
      (!Number.isFinite(Number(form.budgetAmount)) ||
        Number(form.budgetAmount) <= 0)
    ) {
      next.general = "Enter a budget greater than zero or leave it blank.";
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

    const draft: EnquiryDraft = { ...form, target };
    onDraftReady?.(draft);
    setDraftReady(true);
  }

  return (
    <section className={styles.panel} aria-labelledby="project-enquiry-title">
      <header className={styles.panelHeader}>
        <div className={styles.panelHeaderMain}>
          <p className={styles.kicker}>PROJECT ENQUIRY</p>
          <h2 className={styles.panelTitle} id="project-enquiry-title">
            Explore the wider opportunity
          </h2>
          <p className={styles.panelLead}>
            Share your requirements for the project, collection or its available opportunities.
          </p>
        </div>
        <span className={styles.badge}>Project request</span>
      </header>

      <div className={styles.summaryRow}>
        <span className={styles.summaryLabel}>Project</span>
        <span className={styles.summaryValue}>{target.title}</span>
      </div>

      {target.location ? (
        <div className={styles.summaryRow}>
          <span className={styles.summaryLabel}>Location</span>
          <span className={styles.summaryValue}>{target.location}</span>
        </div>
      ) : null}

      <div className={styles.notice} role="note">
        <strong>Preview mode — nothing will be sent</strong>
        <p>{ENQUIRY_SERVICE_NOTICE}</p>
      </div>

      <form className={styles.form} onSubmit={handleSubmit} noValidate>
        <div className={styles.field}>
          <label className={styles.label} htmlFor="project-enquiry-purpose">
            What would you like to explore?
          </label>
          <select
            className={styles.select}
            id="project-enquiry-purpose"
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

        <div className={styles.fieldGrid}>
          <div className={styles.field}>
            <label className={styles.label} htmlFor="project-enquiry-currency">
              Budget currency
            </label>
            <select
              className={styles.select}
              id="project-enquiry-currency"
              value={form.budgetCurrency}
              onChange={(event) =>
                update("budgetCurrency", event.currentTarget.value)
              }
            >
              {ENQUIRY_CURRENCY_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div className={styles.field}>
            <label className={styles.label} htmlFor="project-enquiry-budget">
              Budget ceiling <span className={styles.optional}>Optional</span>
            </label>
            <input
              className={styles.input}
              id="project-enquiry-budget"
              type="number"
              min="0"
              step="any"
              value={form.budgetAmount}
              onChange={(event) =>
                update("budgetAmount", event.currentTarget.value)
              }
              placeholder="Enter amount"
            />
          </div>
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
          idPrefix="project-enquiry"
          fullName={form.fullName}
          email={form.email}
          phone={form.phone}
          preference={form.contactPreference}
          errors={errors}
          onChange={updateContact}
        />

        <EnquiryContactPreference
          idPrefix="project-enquiry-contact"
          value={form.contactPreference}
          onChange={(value: ContactPreference) =>
            update("contactPreference", value)
          }
          error={undefined}
        />

        <div className={styles.field}>
          <label className={styles.label} htmlFor="project-enquiry-message">
            Project requirements or questions
            <span className={styles.optional}>Optional</span>
          </label>
          <textarea
            className={styles.textarea}
            id="project-enquiry-message"
            rows={4}
            maxLength={2000}
            value={form.message}
            onChange={(event) => update("message", event.currentTarget.value)}
            placeholder="Ask about configurations, project context, included amenities or details that need verification."
          />
        </div>

        {errors.general ? (
          <div className={styles.errorBanner} role="alert">
            <p>{errors.general}</p>
          </div>
        ) : null}

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
              I consent to being contacted about this project request if an authorised enquiry service is connected and the request is submitted.
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
          Contact details stay in this component's page state in the current preview. They are not sent to a service or saved to browser storage.
        </p>

        <div className={styles.formActions}>
          <button className={styles.primaryButton} type="submit">
            Review project enquiry <span aria-hidden="true">↗</span>
          </button>
          {target.href ? (
            <a className={styles.secondaryButton} href={target.href}>
              Return to project
            </a>
          ) : null}
        </div>
      </form>

      {draftReady ? (
        <div className={styles.successBanner} role="status" aria-live="polite">
          <strong>Project enquiry draft prepared</strong>
          <p>
            This draft is ready for review in this page only. No request was sent, no reference was created and no project availability was confirmed.
          </p>
        </div>
      ) : null}
    </section>
  );
}
