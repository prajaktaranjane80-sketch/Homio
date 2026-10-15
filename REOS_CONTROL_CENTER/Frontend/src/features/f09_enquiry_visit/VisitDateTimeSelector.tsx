"use client";

import type {
  VisitTimeWindow,
  VisitType,
  VisitValidationErrors,
} from "./visit.types";

import {
  MAX_VISIT_LEAD_DAYS,
  MIN_VISIT_LEAD_DAYS,
  VISIT_TIME_WINDOWS,
  VISIT_TYPE_OPTIONS,
} from "./enquiry.constants";

import styles from "./EnquiryWorkspace.module.css";

type Props = Readonly<{
  visitType: VisitType;
  preferredDate: string;
  preferredTimeWindow: VisitTimeWindow;
  timeZone: string;
  errors: VisitValidationErrors;
  onVisitTypeChange: (value: VisitType) => void;
  onDateChange: (value: string) => void;
  onTimeWindowChange: (value: VisitTimeWindow) => void;
  onTimeZoneChange: (value: string) => void;
  idPrefix?: string;
  disabled?: boolean;
}>;

function getLocalDateOffset(days: number): string {
  const date = new Date();

  date.setHours(12, 0, 0, 0);
  date.setDate(date.getDate() + days);

  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");

  return `${year}-${month}-${day}`;
}

export default function VisitDateTimeSelector({
  visitType,
  preferredDate,
  preferredTimeWindow,
  timeZone,
  errors,
  onVisitTypeChange,
  onDateChange,
  onTimeWindowChange,
  onTimeZoneChange,
  idPrefix = "visit-date-time",
  disabled = false,
}: Props) {
  const typeId = `${idPrefix}-type`;
  const dateId = `${idPrefix}-date`;
  const windowId = `${idPrefix}-window`;
  const timeZoneId = `${idPrefix}-timezone`;

  const minDate = getLocalDateOffset(MIN_VISIT_LEAD_DAYS);
  const maxDate = getLocalDateOffset(MAX_VISIT_LEAD_DAYS);

  return (
    <section
      className={styles.stack}
      aria-labelledby={`${idPrefix}-heading`}
    >
      <div>
        <p className={styles.kicker}>VISIT PREFERENCES</p>

        <h2
          id={`${idPrefix}-heading`}
          className={styles.statusTitle}
        >
          When would you like to visit?
        </h2>

        <p className={styles.fieldHelp}>
          These are your preferred options, not a confirmed
          appointment. Availability must be verified by the
          authorized scheduling service.
        </p>
      </div>

      <div className={styles.field}>
        <label className={styles.label} htmlFor={typeId}>
          Visit format
        </label>

        <select
          className={styles.select}
          id={typeId}
          value={visitType}
          disabled={disabled}
          onChange={(event) => {
            onVisitTypeChange(event.currentTarget.value as VisitType);
          }}
        >
          {VISIT_TYPE_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>

        <p className={styles.fieldHelp}>
          A video walkthrough is also a request and is not booked
          automatically.
        </p>
      </div>

      <div className={styles.fieldGrid}>
        <div className={styles.field}>
          <label className={styles.label} htmlFor={dateId}>
            Preferred date
          </label>

          <input
            className={styles.input}
            id={dateId}
            name="preferredDate"
            type="date"
            value={preferredDate}
            min={minDate}
            max={maxDate}
            required
            disabled={disabled}
            aria-invalid={Boolean(errors.preferredDate)}
            aria-describedby={
              errors.preferredDate
                ? `${dateId}-error`
                : `${dateId}-help`
            }
            onChange={(event) => {
              onDateChange(event.currentTarget.value);
            }}
          />

          {errors.preferredDate ? (
            <p
              className={styles.fieldError}
              id={`${dateId}-error`}
              role="alert"
            >
              {errors.preferredDate}
            </p>
          ) : (
            <p className={styles.fieldHelp} id={`${dateId}-help`}>
              Choose a date between tomorrow and the next 90 days.
            </p>
          )}
        </div>

        <div className={styles.field}>
          <label className={styles.label} htmlFor={windowId}>
            Preferred time window
          </label>

          <select
            className={styles.select}
            id={windowId}
            name="preferredTimeWindow"
            value={preferredTimeWindow}
            disabled={disabled}
            aria-invalid={Boolean(errors.preferredTimeWindow)}
            aria-describedby={
              errors.preferredTimeWindow
                ? `${windowId}-error`
                : `${windowId}-help`
            }
            onChange={(event) => {
              onTimeWindowChange(
                event.currentTarget.value as VisitTimeWindow,
              );
            }}
          >
            {VISIT_TIME_WINDOWS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>

          {errors.preferredTimeWindow ? (
            <p
              className={styles.fieldError}
              id={`${windowId}-error`}
              role="alert"
            >
              {errors.preferredTimeWindow}
            </p>
          ) : (
            <p className={styles.fieldHelp} id={`${windowId}-help`}>
              Times use the time zone entered below.
            </p>
          )}
        </div>
      </div>

      <div className={styles.field}>
        <label className={styles.label} htmlFor={timeZoneId}>
          Time zone
        </label>

        <input
          className={styles.input}
          id={timeZoneId}
          name="timeZone"
          type="text"
          value={timeZone}
          maxLength={100}
          autoComplete="off"
          spellCheck={false}
          placeholder="Europe/London"
          required
          disabled={disabled}
          aria-invalid={Boolean(errors.timeZone)}
          aria-describedby={
            errors.timeZone
              ? `${timeZoneId}-error`
              : `${timeZoneId}-help`
          }
          onChange={(event) => {
            onTimeZoneChange(event.currentTarget.value);
          }}
        />

        {errors.timeZone ? (
          <p
            className={styles.fieldError}
            id={`${timeZoneId}-error`}
            role="alert"
          >
            {errors.timeZone}
          </p>
        ) : (
          <p className={styles.fieldHelp} id={`${timeZoneId}-help`}>
            Use an IANA time-zone name, for example
            Asia/Kolkata, Asia/Singapore, or America/New_York.
          </p>
        )}
      </div>
    </section>
  );
}
