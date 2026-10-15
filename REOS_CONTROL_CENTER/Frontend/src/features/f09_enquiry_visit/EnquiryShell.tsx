"use client";

import { useEffect, useState, type ReactNode } from "react";

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
type WorkspaceMode = "enquiry" | "visit";

type Props = Readonly<{
  target: EnquiryTarget;
  onEnquiryDraftReady?: (draft: EnquiryDraft) => void;
  onVisitDraftReady?: (draft: VisitDraft) => void;
}>;

function isListingTarget(
  target: EnquiryTarget,
): target is ListingTarget {
  return (
    (target.kind === "property" || target.kind === "project") &&
    typeof target.id === "string" &&
    target.id.trim().length > 0 &&
    typeof target.title === "string" &&
    target.title.trim().length > 0
  );
}

function getTargetLabel(kind: EnquiryTarget["kind"]): string {
  if (kind === "property") return "Property";
  if (kind === "project") return "Project";
  return "General enquiry";
}

export default function EnquiryShell({
  target,
  onEnquiryDraftReady,
  onVisitDraftReady,
}: Props) {
  const [mode, setMode] = useState<WorkspaceMode>("enquiry");

  const enquiryAnchorId = `${target.kind}-enquiry-workspace`;
  const visitAnchorId = `${target.kind}-visit-workspace`;
  const enquiryPanelId = `${target.kind}-enquiry-panel`;
  const visitPanelId = `${target.kind}-visit-panel`;
  const headingId = `${target.kind}-enquiry-visit-heading`;

  useEffect(() => {
    function syncModeFromHash() {
      if (
        target.kind !== "general" &&
        window.location.hash === `#${visitAnchorId}`
      ) {
        setMode("visit");
      } else if (window.location.hash === `#${enquiryAnchorId}`) {
        setMode("enquiry");
      }
    }

    window.addEventListener("hashchange", syncModeFromHash);

    return () => {
      window.removeEventListener("hashchange", syncModeFromHash);
    };
  }, [enquiryAnchorId, target.kind, visitAnchorId]);

  const listingTarget = isListingTarget(target) ? target : null;

  const enquiryContent: ReactNode =
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
        This enquiry needs a valid listing ID and title. Open the
        enquiry from a property or project preview that supplies
        its target details.
      </div>
    );

  const visitContent: ReactNode = listingTarget ? (
    <VisitRequestForm
      target={listingTarget}
      onDraftReady={onVisitDraftReady}
    />
  ) : (
    <div className={styles.notice} role="note">
      Visit requests require a specific property or project. A
      general HOMIO enquiry does not create a visit request.
    </div>
  );

  const targetName =
    target.title?.trim() || getTargetLabel(target.kind);

  return (
    <section
      className={styles.workspace}
      aria-labelledby={headingId}
    >
      <div className={styles.container}>
        <header className={styles.hero}>
          <p className={styles.eyebrow}>
            HOMIO · ENQUIRY &amp; VISIT
          </p>

          <h2 className={styles.heroTitle} id={headingId}>
            Make your next move with clarity.
          </h2>

          <p className={styles.heroText}>
            Ask a focused question or prepare a visit request.
            This preview prepares drafts only; it does not submit
            an enquiry or book an appointment.
          </p>

          <div className={styles.heroMeta}>
            <span className={styles.metaPill}>
              {getTargetLabel(target.kind)}
            </span>

            <span className={styles.metaPill}>{targetName}</span>

            {target.location ? (
              <span className={styles.metaPill}>
                {target.location}
              </span>
            ) : null}
          </div>
        </header>

        <div className={styles.layout}>
          <div className={styles.mainColumn}>
            <div className={styles.panel}>
              <p className={styles.kicker}>
                CHOOSE YOUR NEXT STEP
              </p>

              <div
                className={styles.modeSwitch}
                role="group"
                aria-label="Choose enquiry or visit"
              >
                <button
                  id={enquiryAnchorId}
                  className={styles.modeButton}
                  type="button"
                  aria-pressed={mode === "enquiry"}
                  aria-controls={enquiryPanelId}
                  onClick={() => setMode("enquiry")}
                >
                  Prepare an enquiry
                </button>

                {target.kind !== "general" ? (
                  <button
                    id={visitAnchorId}
                    className={styles.modeButton}
                    type="button"
                    aria-pressed={mode === "visit"}
                    aria-controls={visitPanelId}
                    onClick={() => setMode("visit")}
                  >
                    Request a visit
                  </button>
                ) : null}
              </div>

              <p className={styles.fieldHelp}>
                {mode === "enquiry"
                  ? ENQUIRY_SERVICE_NOTICE
                  : VISIT_SERVICE_NOTICE}
              </p>
            </div>

            <div
              id={enquiryPanelId}
              className={styles.shellFormPanel}
              hidden={mode !== "enquiry"}
            >
              {enquiryContent}
            </div>

            {target.kind !== "general" ? (
              <div
                id={visitPanelId}
                className={styles.shellFormPanel}
                hidden={mode !== "visit"}
              >
                {visitContent}
              </div>
            ) : null}
          </div>

          <aside className={styles.sideColumn}>
            <section className={styles.sidePanel}>
              <p className={styles.kicker}>
                A CLEAR, HONEST PREVIEW
              </p>

              <h3 className={styles.panelTitle}>
                Your request stays a draft
              </h3>

              <p className={styles.panelLead}>
                Submission, broker notification, confirmed
                availability and appointment management require
                an authorized service that is not connected in
                this preview.
              </p>

              <div className={styles.notice} role="note">
                Nothing is sent, no reference number is generated,
                and no appointment is booked by preparing a draft.
              </div>

              <p className={styles.privacyNote}>
                Do not include passwords, payment credentials or
                sensitive identity documents in these forms.
              </p>
            </section>
          </aside>
        </div>
      </div>
    </section>
  );
}
