"use client";

import { useState, type FormEvent } from "react";

import EnquiryContactDetails from "./EnquiryContactDetails";
import EnquiryContactPreference from "./EnquiryContactPreference";
import VisitDateTimeSelector from "./VisitDateTimeSelector";

import type {
  ContactPreference,
  EnquiryTarget,
} from "./enquiry.types";

import type {
  VisitDraft,
  VisitTimeWindow,
  VisitType,
  VisitValidationErrors,
} from "./visit.types";

import {
  isValidEmail,
  isValidInternationalPhone,
  isValidVisitDate,
  VISIT_SERVICE_NOTICE,
  VISIT_TIME_WINDOWS,
} from "./enquiry.constants";

import styles from "./EnquiryWorkspace.module.css";

type VisitTarget = Readonly<{
  kind: "property" | "project";
  id: string;
  title: string;
  location?: string;
  href?: string;
}>;

type ContactField = "fullName" | "email" | "phone";

type Props = Readonly<{
  target: VisitTarget;
  onDraftReady?: (draft: VisitDraft) => void;
}>;

function getBrowserTimeZone(): string {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
  } catch {
    return "UTC";
  }
}

function isValidTimeZone(value: string): boolean {
  const normalized = value.trim();

  if (!normalized) {
    return false;
  }

  try {
    new Intl.DateTimeFormat("en-US", {
      timeZone: normalized,
    }).format(new Date());

    return true;
  } catch {
    return false;
  }
}

export default function VisitRequestForm({
  target,
  onDraftReady,
}: Props) {
  const [visitType, setVisitType] = useState<VisitType>("in_person");
  const [preferredDate, setPreferredDate] = useState("");
  const [preferredTimeWindow, setPreferredTimeWindow] =
    useState<VisitTimeWindow>("09:00-11:00");
  const [timeZone, setTimeZone] = useState(getBrowserTimeZone);
  const [attendeeCount, setAttendeeCount] = useState(1);

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [contactPreference, setContactPreference] =
    useState<ContactPreference>("email");

  const [accessibilityNeeds, setAccessibilityNeeds] = useState("");
  const [notes, setNotes] = useState("");
  const [consentToContact, setConsentToContact] = useState(false);

  const [errors, setErrors] = useState<VisitValidationErrors>({});
  const [draftReady, setDraftReady] = useState(false);

  function updateContact(field: ContactField, value: string) {
    if (field === "fullName") {
      setFullName(value);
    } else if (field === "email") {
      setEmail(value);
    } else {
      setPhone(value);
    }

    setErrors((current) => ({
      ...current,
      [field]: undefined,
      general: undefined,
    }));

    setDraftReady(false);
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const nextErrors: VisitValidationErrors = {};

    if (!fullName.trim()) {
      nextErrors.fullName = "Enter your full name.";
    }

    if (contactPreference === "email" && !email.trim()) {
      nextErrors.email = "Enter an email address for contact.";
    } else if (email.trim() && !isValidEmail(email)) {
      nextErrors.email = "Enter a valid email address.";
    }

    if (contactPreference !== "email" && !phone.trim()) {
      nextErrors.phone =
        "Enter a phone number for your selected contact method.";
    } else if (
      phone.trim() &&
      !isValidInternationalPhone(phone)
    ) {
      nextErrors.phone =
        "Enter a valid international phone number, including its country code.";
    }

    if (!isValidVisitDate(preferredDate)) {
      nextErrors.preferredDate =
        "Choose a valid date between tomorrow and the next 90 days.";
    }

    if (
      !VISIT_TIME_WINDOWS.some(
        (option) => option.value === preferredTimeWindow,
      )
    ) {
      nextErrors.preferredTimeWindow =
        "Choose one of the available time windows.";
    }

    if (!isValidTimeZone(timeZone)) {
      nextErrors.timeZone =
        "Enter a valid IANA time-zone name, such as Asia/Kolkata.";
    }

    if (!consentToContact) {
      nextErrors.consentToContact =
        "Consent is required to prepare this contact request.";
    }

    if (Object.keys(nextErrors).length > 0) {
      setErrors(nextErrors);
      setDraftReady(false);
      return;
    }

    const draft: VisitDraft = {
      target: target as EnquiryTarget,
      visitType,
      preferredDate,
      preferredTimeWindow,
      timeZone: timeZone.trim(),
      attendeeCount,
      fullName: fullName.trim(),
      email: email.trim(),
      phone: phone.trim(),
      contactPreference,
      accessibilityNeeds: accessibilityNeeds.trim(),
      notes: notes.trim(),
      consentToContact,
    };

    setErrors({});
    setDraftReady(true);
    onDraftReady?.(draft);
  }

  return (
    <section
      className={styles.workspace}
      aria-labelledby="visit-request-title"
    >
      <div className={styles.container}>
        <header className={styles.hero}>
          <p className={styles.eyebrow}>PROPERTY EXPERIENCE</p>

          <h1 className={styles.heroTitle} id="visit-request-title">
            Request a visit
          </h1>

          <p className={styles.heroText}>
            Share your preferred time and visit format. HOMIO will
            need an authorized scheduling service to submit the
            request and confirm availability.
          </p>

          <div className={styles.heroMeta}>
            <span className={styles.metaPill}>
              {target.kind === "project" ? "Project" : "Property"}
            </span>

            <span className={styles.metaPill}>{target.title}</span>

            {target.location ? (
              <span className={styles.metaPill}>
                {target.location}
              </span>
            ) : null}
          </div>
        </header>

        <div className={styles.layout}>
          <div className={styles.mainColumn}>
            <section className={styles.panel}>
              <div className={styles.panelHeader}>
                <div className={styles.panelHeaderMain}>
                  <p className={styles.kicker}>VISIT REQUEST</p>

                  <h2 className={styles.panelTitle}>
                    Your preferred arrangements
                  </h2>

                  <p className={styles.panelLead}>
                    Complete the details below to prepare a request
                    draft. This will not book an appointment.
                  </p>
                </div>
              </div>

              <form
                className={styles.form}
                onSubmit={handleSubmit}
                noValidate
              >
                <VisitDateTimeSelector
                  visitType={visitType}
                  preferredDate={preferredDate}
                  preferredTimeWindow={preferredTimeWindow}
                  timeZone={timeZone}
                  errors={errors}
                  onVisitTypeChange={(value) => {
                    setVisitType(value);
                    setDraftReady(false);
                  }}
                  onDateChange={(value) => {
                    setPreferredDate(value);
                    setErrors((current) => ({
                      ...current,
                      preferredDate: undefined,
                    }));
                    setDraftReady(false);
                  }}
                  onTimeWindowChange={(value) => {
                    setPreferredTimeWindow(value);
                    setErrors((current) => ({
                      ...current,
                      preferredTimeWindow: undefined,
                    }));
                    setDraftReady(false);
                  }}
                  onTimeZoneChange={(value) => {
                    setTimeZone(value);
                    setErrors((current) => ({
                      ...current,
                      timeZone: undefined,
                    }));
                    setDraftReady(false);
                  }}
                  idPrefix="visit-request-schedule"
                />

                <div className={styles.separator} />

                <div className={styles.field}>
                  <label
                    className={styles.label}
                    htmlFor="visit-attendee-count"
                  >
                    Number of attendees
                  </label>

                  <select
                    className={styles.select}
                    id="visit-attendee-count"
                    value={attendeeCount}
                    onChange={(event) => {
                      setAttendeeCount(
                        Number(event.currentTarget.value),
                      );
                      setDraftReady(false);
                    }}
                  >
                    {[1, 2, 3, 4, 5, 6].map((count) => (
                      <option key={count} value={count}>
                        {count} {count === 1 ? "person" : "people"}
                      </option>
                    ))}
                  </select>
                </div>

                <div className={styles.field}>
                  <label
                    className={styles.label}
                    htmlFor="visit-accessibility"
                  >
                    Accessibility or access needs
                    <span className={styles.optional}>Optional</span>
                  </label>

                  <textarea
                    className={styles.textarea}
                    id="visit-accessibility"
                    value={accessibilityNeeds}
                    maxLength={1000}
                    rows={3}
                    onChange={(event) => {
                      setAccessibilityNeeds(
                        event.currentTarget.value,
                      );
                      setDraftReady(false);
                    }}
                    placeholder="Share any access arrangements we should consider."
                  />
                </div>

                <div className={styles.field}>
                  <label
                    className={styles.label}
                    htmlFor="visit-notes"
                  >
                    Additional notes
                    <span className={styles.optional}>Optional</span>
                  </label>

                  <textarea
                    className={styles.textarea}
                    id="visit-notes"
                    value={notes}
                    maxLength={2000}
                    rows={4}
                    onChange={(event) => {
                      setNotes(event.currentTarget.value);
                      setDraftReady(false);
                    }}
                    placeholder="Questions or preferences about the visit."
                  />
                </div>

                <div className={styles.separator} />

                <EnquiryContactDetails
                  fullName={fullName}
                  email={email}
                  phone={phone}
                  preference={contactPreference}
                  idPrefix="visit-request-contact"
                  errors={errors}
                  onChange={updateContact}
                />

                <EnquiryContactPreference
                  value={contactPreference}
                  idPrefix="visit-request-preference"
                  onChange={(value) => {
                    setContactPreference(value);
                    setDraftReady(false);
                  }}
                />

                <div className={styles.consentBlock}>
                  <label
                    className={styles.consentLine}
                    htmlFor="visit-contact-consent"
                  >
                    <input
                      id="visit-contact-consent"
                      name="consentToContact"
                      type="checkbox"
                      checked={consentToContact}
                      aria-invalid={Boolean(errors.consentToContact)}
                      aria-describedby={
                        errors.consentToContact
                          ? "visit-contact-consent-error"
                          : undefined
                      }
                      onChange={(event) => {
                        setConsentToContact(
                          event.currentTarget.checked,
                        );
                        setErrors((current) => ({
                          ...current,
                          consentToContact: undefined,
                        }));
                        setDraftReady(false);
                      }}
                    />

                    <span>
                      I agree that HOMIO may use these details for
                      this visit request, subject to the applicable
                      privacy notice.
                    </span>
                  </label>

                  {errors.consentToContact ? (
                    <p
                      className={styles.fieldError}
                      id="visit-contact-consent-error"
                      role="alert"
                    >
                      {errors.consentToContact}
                    </p>
                  ) : null}
                </div>

                <p className={styles.privacyNote}>
                  This preview keeps the draft in page state only.
                  It does not submit, persist, or notify anyone about
                  the request.
                </p>

                {errors.general ? (
                  <div className={styles.errorBanner} role="alert">
                    {errors.general}
                  </div>
                ) : null}

                <div className={styles.formActions}>
                  <button
                    className={styles.primaryButton}
                    type="submit"
                  >
                    Prepare visit request draft
                    <span aria-hidden="true"> ↗</span>
                  </button>

                  {target.href ? (
                    <a
                      className={styles.secondaryButton}
                      href={target.href}
                    >
                      Return to listing
                    </a>
                  ) : null}
                </div>
              </form>

              {draftReady ? (
                <div className={styles.notice} role="status" aria-live="polite">
                  <strong>Visit request draft prepared — not booked.</strong>

                  <p>{VISIT_SERVICE_NOTICE}</p>

                  <p>
                    Preferred date: {preferredDate}. Preferred
                    window:{" "}
                    {
                      VISIT_TIME_WINDOWS.find(
                        (option) =>
                          option.value === preferredTimeWindow,
                      )?.label
                    }{" "}
                    ({timeZone.trim()}).
                  </p>
                </div>
              ) : null}
            </section>
          </div>

          <aside className={styles.sideColumn}>
            <section className={styles.sidePanel}>
              <p className={styles.kicker}>BEFORE YOU CONTINUE</p>

              <h2 className={styles.panelTitle}>
                A request is not a booking
              </h2>

              <p className={styles.panelLead}>
                Your selected date and time are preferences only.
                Availability, host coordination, and final
                confirmation require the authorized scheduling
                service.
              </p>

              <div className={styles.notice}>
                {VISIT_SERVICE_NOTICE}
              </div>
            </section>
          </aside>
        </div>
      </div>
    </section>
  );
}
