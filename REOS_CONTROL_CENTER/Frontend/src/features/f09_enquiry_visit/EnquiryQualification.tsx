"use client";

import type {
  EnquiryQualification as QualificationValue,
  EnquiryTimeframe,
} from "./enquiry.types";

import {
  ENQUIRY_QUALIFICATION_OPTIONS,
  ENQUIRY_TIMEFRAME_OPTIONS,
} from "./enquiry.constants";

import styles from "./EnquiryWorkspace.module.css";

type Props = Readonly<{
  qualification: QualificationValue;
  timeframe: EnquiryTimeframe;
  onQualificationChange: (value: QualificationValue) => void;
  onTimeframeChange: (value: EnquiryTimeframe) => void;
  disabled?: boolean;
}>;

export default function EnquiryQualification({
  qualification,
  timeframe,
  onQualificationChange,
  onTimeframeChange,
  disabled = false,
}: Props) {
  return (
    <section className={styles.stack} aria-labelledby="enquiry-qualification-title">
      <div className={styles.field}>
        <label
          className={styles.label}
          htmlFor="enquiry-qualification"
          id="enquiry-qualification-title"
        >
          Where are you in your property journey?
        </label>

        <select
          className={styles.select}
          id="enquiry-qualification"
          value={qualification}
          disabled={disabled}
          onChange={(event) => {
            onQualificationChange(
              event.currentTarget.value as QualificationValue,
            );
          }}
        >
          {ENQUIRY_QUALIFICATION_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      <div className={styles.field}>
        <label
          className={styles.label}
          htmlFor="enquiry-timeframe"
        >
          Preferred timeframe
        </label>

        <select
          className={styles.select}
          id="enquiry-timeframe"
          value={timeframe}
          disabled={disabled}
          onChange={(event) => {
            onTimeframeChange(
              event.currentTarget.value as EnquiryTimeframe,
            );
          }}
        >
          {ENQUIRY_TIMEFRAME_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>

        <p className={styles.fieldHelp}>
          This is a planning preference, not a promise of property availability or response time.
        </p>
      </div>
    </section>
  );
}
