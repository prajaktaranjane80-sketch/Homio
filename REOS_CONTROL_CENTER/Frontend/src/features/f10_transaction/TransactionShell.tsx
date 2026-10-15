
"use client";

import {
  useId,
  useRef,
  useState,
  type KeyboardEvent,
} from "react";

import DealCompletion from "./DealCompletion";
import DealOverview from "./DealOverview";
import DealParties from "./DealParties";
import DealProperty from "./DealProperty";
import CommissionStatus from "./CommissionStatus";
import DocumentChecklist from "./DocumentChecklist";
import NegotiationPanel from "./NegotiationPanel";
import OfferSummary from "./OfferSummary";
import TransactionAccessNotice from "./TransactionAccessNotice";
import TransactionEmptyState from "./TransactionEmptyState";
import TransactionFinancialStatus from "./TransactionFinancialStatus";
import TransactionMilestones from "./TransactionMilestones";
import TransactionStatusPanel from "./TransactionStatus";

import type {
  TransactionActionRequestHandler,
  TransactionRecord,
  TransactionViewerRole,
} from "./transaction.types";
import styles from "./TransactionWorkspace.module.css";

type WorkspaceTab = "overview" | "documents" | "timeline";

type Props = Readonly<{
  transaction?: TransactionRecord;
  viewerRole?: TransactionViewerRole;
  onActionRequest?: TransactionActionRequestHandler;
}>;

const TABS: ReadonlyArray<{
  id: WorkspaceTab;
  label: string;
}> = [
  { id: "overview", label: "Overview" },
  { id: "documents", label: "Documents" },
  { id: "timeline", label: "Timeline & negotiation" },
];

export default function TransactionShell({
  transaction,
  viewerRole,
  onActionRequest,
}: Props) {
  const [activeTab, setActiveTab] =
    useState<WorkspaceTab>("overview");

  const generatedId = useId().replace(/:/g, "");
  const tabListId = `f10-tabs-${generatedId}`;

  const tabRefs = useRef<
    Record<WorkspaceTab, HTMLButtonElement | null>
  >({
    overview: null,
    documents: null,
    timeline: null,
  });

  function handleTabKeyDown(
    event: KeyboardEvent<HTMLButtonElement>,
    currentTab: WorkspaceTab,
  ) {
    const currentIndex = TABS.findIndex(
      (tab) => tab.id === currentTab,
    );

    let nextIndex = currentIndex;

    switch (event.key) {
      case "ArrowRight":
        nextIndex = (currentIndex + 1) % TABS.length;
        break;
      case "ArrowLeft":
        nextIndex =
          (currentIndex - 1 + TABS.length) % TABS.length;
        break;
      case "Home":
        nextIndex = 0;
        break;
      case "End":
        nextIndex = TABS.length - 1;
        break;
      default:
        return;
    }

    event.preventDefault();

    const nextTab = TABS[nextIndex].id;
    setActiveTab(nextTab);
    tabRefs.current[nextTab]?.focus();
  }

  if (!transaction) {
    return <TransactionEmptyState />;
  }

  return (
    <main className={styles.workspace}>
      <header className={styles.pageHead}>
        <div className={styles.pageHeadMain}>
          <nav className={styles.breadcrumb} aria-label="Breadcrumb">
            <span>My HOMIO</span>
            <span aria-hidden="true">/</span>
            <span>Transactions</span>
            <span aria-hidden="true">/</span>
            <span aria-current="page">Workspace</span>
          </nav>

          <p className={styles.eyebrow}>
            F10 · TRANSACTION WORKSPACE
          </p>
          <h1 className={styles.pageTitle}>
            Transaction workspace
          </h1>
          <p className={styles.pageDescription}>
            A clear view of transaction progress, documents and the
            next permitted action.
          </p>
        </div>

        <div className={styles.pageHeadMeta}>
          <TransactionStatusPanel
            status={transaction.status}
            updatedAt={transaction.updatedAt}
          />
          <span className={styles.referencePill}>
            {transaction.reference || "Reference not supplied"}
          </span>
        </div>
      </header>

      <TransactionAccessNotice viewerRole={viewerRole} />

      <DealOverview
        transaction={transaction}
        onActionRequest={onActionRequest}
      />

      <div
        id={tabListId}
        className={styles.tabList}
        role="tablist"
        aria-label="Transaction workspace sections"
      >
        {TABS.map((tab) => {
          const selected = activeTab === tab.id;
          const tabId = `${tabListId}-${tab.id}`;
          const panelId = `${tabId}-panel`;

          return (
            <button
              key={tab.id}
              ref={(node) => {
                tabRefs.current[tab.id] = node;
              }}
              type="button"
              id={tabId}
              role="tab"
              aria-selected={selected}
              aria-controls={panelId}
              tabIndex={selected ? 0 : -1}
              className={`${styles.tabButton} ${
                selected ? styles.tabButtonActive : ""
              }`}
              onClick={() => setActiveTab(tab.id)}
              onKeyDown={(event) =>
                handleTabKeyDown(event, tab.id)
              }
            >
              {tab.label}

              {tab.id === "documents" ? (
                <span className={styles.tabCount}>
                  {transaction.documents.length}
                </span>
              ) : null}

              {tab.id === "timeline" ? (
                <span className={styles.tabCount}>
                  {transaction.milestones.length}
                </span>
              ) : null}
            </button>
          );
        })}
      </div>

      <section
        id={`${tabListId}-overview-panel`}
        role="tabpanel"
        aria-labelledby={`${tabListId}-overview`}
        hidden={activeTab !== "overview"}
        className={styles.tabPanel}
        tabIndex={0}
      >
        <div className={styles.contentGrid}>
          <div className={styles.mainColumn}>
            <DealProperty property={transaction.property} />
            <OfferSummary offer={transaction.offer} />
            <TransactionFinancialStatus
              summary={transaction.financial}
            />
            <DealCompletion completion={transaction.completion} />
          </div>

          <aside
            className={styles.sideColumn}
            aria-label="Transaction details"
          >
            <DealParties parties={transaction.parties} />
            <CommissionStatus commission={transaction.commission} />
          </aside>
        </div>
      </section>

      <section
        id={`${tabListId}-documents-panel`}
        role="tabpanel"
        aria-labelledby={`${tabListId}-documents`}
        hidden={activeTab !== "documents"}
        className={styles.tabPanel}
        tabIndex={0}
      >
        <div className={styles.singleColumn}>
          <DocumentChecklist
            documents={transaction.documents}
            onActionRequest={onActionRequest}
          />
        </div>
      </section>

      <section
        id={`${tabListId}-timeline-panel`}
        role="tabpanel"
        aria-labelledby={`${tabListId}-timeline`}
        hidden={activeTab !== "timeline"}
        className={styles.tabPanel}
        tabIndex={0}
      >
        <div className={styles.singleColumn}>
          <TransactionMilestones
            milestones={transaction.milestones}
          />
          <NegotiationPanel
            entries={transaction.negotiations}
            onActionRequest={onActionRequest}
          />
        </div>
      </section>

      <footer className={styles.workspaceFooter}>
        <span className={styles.footerMark} aria-hidden="true">
          H
        </span>
        <p>
          HOMIO presents the transaction data it receives. Authorization,
          document verification, payment settlement and transaction status
          remain with the responsible REOS services.
        </p>
      </footer>
    </main>
  );
}
