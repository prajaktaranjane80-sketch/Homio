
"use client";

import { useId } from "react";

import { AREA_UNIT_OPTIONS } from "./market-activation.constants";
import styles from "./MarketFieldSelectors.module.css";

import type { AreaUnit } from "./market-activation.types";

type UnitSelectorProps = Readonly<{
  value: AreaUnit;
  onChange: (unit: AreaUnit) => void;
  disabled?: boolean;
  label?: string;
  id?: string;
}>;

export default function UnitSelector({
  value,
  onChange,
  disabled = false,
  label = "Area measurement",
  id,
}: UnitSelectorProps) {
  const generatedId = useId();
  const selectId = id ?? `f12-unit-${generatedId}`;
  const hintId = `${selectId}-hint`;

  return (
    <div className={styles.fieldCard}>
      <div className={styles.fieldHead}>
        <label className={styles.fieldLabel} htmlFor={selectId}>
          {label}
        </label>
        <span className={styles.fieldHint}>Measurement convention</span>
      </div>

      <div className={styles.controlShell}>
        <span className={styles.leadingMark} aria-hidden="true">
          ↔
        </span>

        <select
          id={selectId}
          className={styles.select}
          value={value}
          disabled={disabled}
          onChange={(event) => {
            const nextValue = AREA_UNIT_OPTIONS.find(
              (unit) => unit.value === event.currentTarget.value,
            );

            if (nextValue) onChange(nextValue.value);
          }}
          aria-describedby={hintId}
        >
          {AREA_UNIT_OPTIONS.map((unit) => (
            <option key={unit.value} value={unit.value}>
              {unit.label} ({unit.shortLabel})
            </option>
          ))}
        </select>

        <span className={styles.chevron} aria-hidden="true">
          <svg viewBox="0 0 16 16" width="16" height="16" fill="none">
            <path
              d="m3.5 5.75 4.5 4.5 4.5-4.5"
              stroke="currentColor"
              strokeWidth="1.6"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </span>
      </div>

      <p className={styles.footnote} id={hintId}>
        This changes the selected convention only. Convert numeric values only when verified source data and conversion rules are available.
      </p>
    </div>
  );
}
