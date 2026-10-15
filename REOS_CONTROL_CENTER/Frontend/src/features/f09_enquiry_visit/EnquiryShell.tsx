"use client";

import { useState } from "react";

import type { EnquiryDraft, EnquiryTarget } from "./enquiry.types";
import type { VisitDraft } from "./visit.types";

import GeneralEnquiryForm from "./GeneralEnquiryForm";
import ProjectEnquiryForm from "./ProjectEnquiryForm";
import PropertyEnquiryForm from "./PropertyEnquiryForm";
import VisitRequestForm from "./VisitRequestForm";

import {
  ENQUIRY_SERVICE_NOTICE,
  VISIT_SERVICE_NOTICE,
} from "./enquiry.constants";

import styles from "./EnquiryWorkspace.module.css";

type PropertyTarget = Readonly<{
  kind: "property";
  id: string;
  title: string;
  location?: string;
  href?: string;
}>;

type ProjectTarget = Readonly<{
  kind: "project";
  id: string;
  title: string;
  location?: string;
  href?: string;
}>;

type ListingTarget = PropertyTarget | ProjectTarget;
export type EnquiryWorkspaceMode = "enquiry" | "visit";

type Props = Readonly<{
  target: EnquiryTarget;
  initialMode?: EnquiryWorkspaceMode;
  onEnquiryDraftReady?: (draft: EnquiryDraft) => void;
  onVisitDraftReady?: (draft: VisitDraft) => void;
}>;

function isListingTarget(target: EnquiryTarget): target is ListingTarget {
  return (
    (target.kind === "property" || target.kind === "project") &&
    typeof target.id === "string" &&
    target.id.trim().length > 0 &&
    typeof target.title === "string" &&
    target.title.trim().length > 0
  );
}

export default function EnquiryShell({
  target,
  initialMode = "enquiry",
  onEnquiryDraftReady,
  onVisitDraftReady,
}: Props) {
  const listingTarget = isListingTarget(target) ? target : null;

  const [mode, setMode] = useState<EnquiryWorkspaceMode>(
    initialMode === "visit" && listingTarget ? "visit" : "enquiry",
  );

  const enquiryPanelId = `${target.kind}-enquiry-panel`;
  const visitPanelId = `${target.kind}-visit-panel`;

  const targetLabel =
    target.kind === "property"
      ? "property"
      : target.kind === "project"
        ? "project"
        : "general enquiry";

  const targetName = target.title?.trim() || "HOMIO";

  const enquiryContent =
    target.kind === "general" ? (
      <GeneralEnquiryForm onDraftReady={onEnquiryDraftReady} />
    ) : listingTarget?.kind === "property" ? (
      <PropertyEnquiryForm
        target={listingTarget}
        onDraftReady={onEnquiryDraftReady}
      />
    ) : listingTarget?.kind === "project" ? (
      <ProjectEnquiryForm
        target={listingTarget}
        onDraftReady={onEnquiryDraftReady}
      />
    ) : (
      <div className={styles.errorBanner} role="alert">
        This enquiry needs a valid listing ID and title. Open it from an
        available property or project preview.
      </div>
    );

  const visitContent = listingTarget ? (
    <VisitRequestForm
      target={listingTarget}
      onDraftReady={onVisitDraftReady}
    />
  ) : (
    <div className={styles.notice} role="note">
      Visit requests require a specific property or project. A general
      enquiry does not create a visit request.
    </div>
  );

  return (
    <>
      {listingTarget ? (
        <div className={styles.container}>
          <section
            className={styles.panel}
            style={{ marginTop: 24, marginBottom: 0 }}
            aria-labelledby="f09-mode-heading"
          >
            <p className={styles.kicker}>YOUR NEXT STEP</p>

            <h2 className={styles.panelTitle} id="f09-mode-heading">
              Contact about this {targetLabel}
            </h2>

            <p className={styles.panelLead}>
              {targetName}
              {target.location ? ` · ${target.location}` : ""}. Choose what
              you would like to prepare. These forms do not send a request or
              book an appointment.
            </p>

            <div
              className={styles.modeSwitch}
              role="group"
              aria-label="Choose enquiry or visit"
            >
              <button
                className={styles.modeButton}
                type="button"
                aria-pressed={mode === "enquiry"}
                aria-controls={enquiryPanelId}
                onClick={() => setMode("enquiry")}
              >
                Prepare an enquiry
              </button>

              <button
                className={styles.modeButton}
                type="button"
                aria-pressed={mode === "visit"}
                aria-controls={visitPanelId}
                onClick={() => setMode("visit")}
              >
                Prepare a visit request
              </button>
            </div>

            <p className={styles.fieldHelp} role="status" aria-live="polite">
              {mode === "enquiry"
                ? ENQUIRY_SERVICE_NOTICE
                : VISIT_SERVICE_NOTICE}
            </p>
          </section>
        </div>
      ) : null}

      <div id={enquiryPanelId} hidden={mode !== "enquiry"}>
        {enquiryContent}
      </div>

      {listingTarget ? (
        <div id={visitPanelId} hidden={mode !== "visit"}>
          {visitContent}
        </div>
      ) : null}
    </>
  );
}
