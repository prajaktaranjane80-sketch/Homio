"use client";

import { useState, type FormEvent } from "react";

import type {
  VisitActionDraft,
  VisitTimeWindow,
} from "./visit.types";

import {
  isValidVisitDate,
  MAX_VISIT_LEAD_DAYS,
  MIN_VISIT_LEAD_DAYS,
  VISIT_TIME_WINDOWS,
} from "./enquiry.constants";

import styles from "./EnquiryWorkspace.module.css";

type Props = Readonly<{
  reference: string;
  timeZone?: string;
  currentDate?: string;
  currentTimeWindow?: VisitTimeWindow;
  onDraftReady?: (draft: VisitActionDraft) => void;
}>;

type FormErrors = Partial<
  Record<
    "reference" | "preferredDate" | "preferredTimeWindow" | "timeZone" | "reason",
    string
  >
>;

function getBrowserTimeZone(): string {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
  } catch {
    return "UTC";
  }
}

function getLocalDateOffset(days: number): string {
  const date = new Date();

  date.setHours(12, 0, 0, 0);
  date.setDate(date.getDate() + days);

  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");

  return `${year}-${month}-${day}`;
}

function isValidTimeZone(value: string): boolean {
  if (!value.trim()) return false;

  try {
    new Intl.DateTimeFormat("en-US", {
      timeZone: value.trim(),
    }).format(new Date());

    return true;
  } catch {
    return false;
  }
}

export default function VisitReschedule({
  reference,
  timeZone: initialTimeZone,
  currentDate,
  currentTimeWindow,
  onDraftReady,
}: Props) {
  const [preferredDate, setPreferredDate] = useState(currentDate ?? "");
  const [preferredTimeWindow, setPreferredTimeWindow] =
    useState<VisitTimeWindow>(
      currentTimeWindow ?? "09:00-11:00",
    );
  const [timeZone, setTimeZone] = useState(
    initialTimeZone || getBrowserTimeZone(),
  );
  const [reason, setReason] = useState("");
  const [errors, setErrors] = useState<FormErrors>({});
  const [draftReady, setDraftReady] = useState(false);

  const minDate = getLocalDateOffset(MIN_VISIT_LEAD_DAYS);
  const maxDate = getLocalDateOffset(MAX_VISIT_LEAD_DAYS);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const nextErrors: FormErrors = {};

    if (!reference.trim()) {
      nextErrors.reference =
        "A valid visit reference is required to prepare a reschedule request.";
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
        "Choose a valid preferred time window.";
    }

    if (!isValidTimeZone(timeZone)) {
      nextErrors.timeZone =
        "Enter a valid IANA time-zone name, such as Asia/Kolkata.";
    }

    if (!reason.trim()) {
      nextErrors.reason =
        "Please tell us briefly why you need to reschedule.";
    }

    if (Object.keys(nextErrors).length > 0) {
      setErrors(nextErrors);
      setDraftReady(false);
      return;
    }

    const draft: VisitActionDraft = {
      reference: reference.trim(),
      action: "reschedule",
      reason: reason.trim(),
      preferredDate,
      preferredTimeWindow,
      timeZone: timeZone.trim(),
    };

    setErrors({});
    setDraftReady(true);
    onDraftReady?.(draft);
  }

  return (
    <section
      className={styles.panel}
      aria-labelledby="visit-reschedule-heading"
    >
      <div className={styles.panelHeader}>
        <div className={styles.panelHeaderMain}>
          <p className={styles.kicker}>VISIT MANAGEMENT</p>

          <h2
            className={styles.panelTitle}
            id="visit-reschedule-heading"
          >
            Request a different time
          </h2>

          <p className={styles.panelLead}>
            Share a new preference for an existing visit. This
            prepares a draft only; it does not change your booking.
          </p>
        </div>
      </div>

      <form
        className={styles.form}
        onSubmit={handleSubmit}
        noValidate
      >
        <div className={styles.field}>
          <span className={styles.label}>Visit reference</span>

          <p className={styles.summaryValue}>
            {reference.trim() || "No reference supplied"}
          </p>

          {errors.reference ? (
            <p className={styles.fieldError} role="alert">
              {errors.reference}
            </p>
          ) : null}
        </div>

        <div className={styles.fieldGrid}>
          <div className={styles.field}>
            <label
              className={styles.label}
              htmlFor="visit-reschedule-date"
            >
              Preferred new date
            </label>

            <input
              className={styles.input}
              id="visit-reschedule-date"
              type="date"
              value={preferredDate}
              min={minDate}
              max={maxDate}
              required
              aria-invalid={Boolean(errors.preferredDate)}
              aria-describedby={
                errors.preferredDate
                  ? "visit-reschedule-date-error"
                  : "visit-reschedule-date-help"
              }
              onChange={(event) => {
                setPreferredDate(event.currentTarget.value);
                setErrors((current) => ({
                  ...current,
                  preferredDate: undefined,
                }));
                setDraftReady(false);
              }}
            />

            {errors.preferredDate ? (
              <p
                className={styles.fieldError}
                id="visit-reschedule-date-error"
                role="alert"
              >
                {errors.preferredDate}
              </p>
            ) : (
              <p
                className={styles.fieldHelp}
                id="visit-reschedule-date-help"
              >
                Select a date between tomorrow and the next 90 days.
              </p>
            )}
          </div>

          <div className={styles.field}>
            <label
              className={styles.label}
              htmlFor="visit-reschedule-window"
            >
              Preferred time window
            </label>

            <select
              className={styles.select}
              id="visit-reschedule-window"
              value={preferredTimeWindow}
              aria-invalid={Boolean(errors.preferredTimeWindow)}
              onChange={(event) => {
                setPreferredTimeWindow(
                  event.currentTarget.value as VisitTimeWindow,
                );
                setErrors((current) => ({
                  ...current,
                  preferredTimeWindow: undefined,
                }));
                setDraftReady(false);
              }}
            >
              {VISIT_TIME_WINDOWS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>

            {errors.preferredTimeWindow ? (
              <p className={styles.fieldError} role="alert">
                {errors.preferredTimeWindow}
              </p>
            ) : null}
          </div>
        </div>

        <div className={styles.field}>
          <label
            className={styles.label}
            htmlFor="visit-reschedule-timezone"
          >
            Time zone
          </label>

          <input
            className={styles.input}
            id="visit-reschedule-timezone"
            value={timeZone}
            maxLength={100}
            required
            placeholder="Asia/Kolkata"
            aria-invalid={Boolean(errors.timeZone)}
            onChange={(event) => {
              setTimeZone(event.currentTarget.value);
              setErrors((current) => ({
                ...current,
                timeZone: undefined,
              }));
              setDraftReady(false);
            }}
          />

          {errors.timeZone ? (
            <p className={styles.fieldError} role="alert">
              {errors.timeZone}
            </p>
          ) : (
            <p className={styles.fieldHelp}>
              Use an IANA time-zone name, for example
              Europe/London or Asia/Singapore.
            </p>
          )}
        </div>

        <div className={styles.field}>
          <label
            className={styles.label}
            htmlFor="visit-reschedule-reason"
          >
            Reason for rescheduling
          </label>

          <textarea
            className={styles.textarea}
            id="visit-reschedule-reason"
            value={reason}
            rows={3}
            maxLength={1000}
            required
            aria-invalid={Boolean(errors.reason)}
            onChange={(event) => {
              setReason(event.currentTarget.value);
              setErrors((current) => ({
                ...current,
                reason: undefined,
              }));
              setDraftReady(false);
            }}
            placeholder="Tell us why the current time no longer works."
          />

          {errors.reason ? (
            <p className={styles.fieldError} role="alert">
              {errors.reason}
            </p>
          ) : null}
        </div>

        <div className={styles.notice} role="note">
          Your existing visit will not change unless the authorized
          scheduling service processes and confirms a new arrangement.
        </div>

        <div className={styles.formActions}>
          <button className={styles.primaryButton} type="submit">
            Prepare reschedule draft
          </button>
        </div>
      </form>

      {draftReady ? (
        <div className={styles.successBanner} role="status" aria-live="polite">
          <strong>Reschedule draft prepared — not submitted.</strong>
          <p>
            No booking was changed and no scheduling team was notified.
          </p>
        </div>
      ) : null}
    </section>
  );
}
