"use client";

import { useState } from "react";

import { Button } from "@/components/ui/Button";

import styles from "./PostProperty.module.css";
import type { PostPropertySubmissionResult } from "./post-property.types";

type Props = Readonly<{
  ready: boolean;
  onSubmit?: () => Promise<PostPropertySubmissionResult>;
  disabled?: boolean;
}>;

export default function PostPropertySubmit({
  ready,
  onSubmit,
  disabled = false,
}: Props) {
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState("");
  const [reference, setReference] = useState("");
  const [accepted, setAccepted] = useState(false);

  async function submit() {
    if (!onSubmit || !ready || disabled || submitting) return;

    setSubmitting(true);
    setMessage("");
    setReference("");
    setAccepted(false);

    try {
      const result = await onSubmit();

      if (result.accepted) {
        setAccepted(true);
        setReference(result.reference?.trim() ?? "");
        setMessage(
          result.message?.trim() ||
            "The service accepted the submission request.",
        );
      } else {
        setMessage(
          result.message?.trim() ||
            "The service did not accept the submission.",
        );
      }
    } catch {
      setMessage(
        "Submission could not be confirmed. Check the service status before trying again.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className={styles.postPanel}>
      <header className={styles.postPanelHeader}>
        <h2 className={styles.postPanelTitle}>Request submission</h2>
        <p className={styles.postPanelDescription}>
          This action requires a connected, authorized submission service. The
          interface itself cannot publish inventory.
        </p>
      </header>

      {!ready ? (
        <p className={styles.postNotice}>
          The draft is not marked ready. Complete required fields and
          verification steps before submitting.
        </p>
      ) : null}

      {!onSubmit ? (
        <p className={styles.postNotice}>
          The property-submission service is not connected. No submission has
          been sent.
        </p>
      ) : null}

      <div className={styles.postActions} aria-busy={submitting}>
        <Button
          type="button"
          disabled={!ready || disabled || submitting || !onSubmit}
          onClick={submit}
        >
          {submitting ? "Submitting…" : "Submit property"}
        </Button>
      </div>

      {message ? (
        <div
          className={`${styles.postState} ${accepted ? styles.postSuccess : ""}`}
          role={accepted ? "status" : "alert"}
        >
          <span className={styles.postStateIcon} aria-hidden="true">
            {accepted ? "✓" : "!"}
          </span>
          <div>
            <h3 className={styles.postStateTitle}>
              {accepted ? "Submission accepted by service" : "Submission not confirmed"}
            </h3>
            <p className={styles.postStateDescription}>{message}</p>
            {reference ? (
              <p className={styles.postStateDescription}>Reference: {reference}</p>
            ) : null}
          </div>
        </div>
      ) : null}
    </section>
  );
}
