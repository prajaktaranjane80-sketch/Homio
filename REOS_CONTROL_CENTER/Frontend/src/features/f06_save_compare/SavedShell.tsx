"use client";

import { useMemo, useState } from "react";

import type {
  PersistenceStatus,
  RecentViewRecord,
  SavedEntityKind,
  SavedRecord,
  SavedSearchRecord,
  SavedTab,
} from "./saved.types";

import SavedProperties from "./SavedProperties";
import SavedProjects from "./SavedProjects";
import SavedLocalities from "./SavedLocalities";
import SavedSearches from "./SavedSearches";
import RecentViews from "./RecentViews";

import styles from "./SavedCompareExperience.module.css";

type SavedShellProps = Readonly<{
  records?: readonly SavedRecord[];
  searches?: readonly SavedSearchRecord[];
  recentViews?: readonly RecentViewRecord[];
  persistenceStatus?: PersistenceStatus;

  onRemoveRecord?: (
    id: string,
    kind: SavedEntityKind,
  ) => void;

  onRemoveSearch?: (id: string) => void;
}>;

const TABS: ReadonlyArray<{
  id: SavedTab;
  label: string;
}> = [
  { id: "properties", label: "Properties" },
  { id: "projects", label: "Projects" },
  { id: "localities", label: "Locations" },
  { id: "searches", label: "Searches" },
  { id: "recent", label: "Recently viewed" },
];

export default function SavedShell({
  records = [],
  searches = [],
  recentViews = [],
  persistenceStatus = "not-connected",
  onRemoveRecord,
  onRemoveSearch,
}: SavedShellProps) {
  const [activeTab, setActiveTab] =
    useState<SavedTab>("properties");

  const [query, setQuery] = useState("");

  const normalizedQuery = query
    .trim()
    .toLocaleLowerCase();

  const visibleRecords = useMemo(
    () =>
      records.filter((item) =>
        [
          item.title,
          item.subtitle ?? "",
          item.detailLine ?? "",
        ]
          .join(" ")
          .toLocaleLowerCase()
          .includes(normalizedQuery),
      ),
    [records, normalizedQuery],
  );

  const visibleSearches = useMemo(
    () =>
      searches.filter((item) =>
        [
          item.title,
          item.filtersSummary ?? "",
        ]
          .join(" ")
          .toLocaleLowerCase()
          .includes(normalizedQuery),
      ),
    [searches, normalizedQuery],
  );

  const visibleRecent = useMemo(
    () =>
      recentViews.filter((item) =>
        [
          item.title,
          item.subtitle ?? "",
        ]
          .join(" ")
          .toLocaleLowerCase()
          .includes(normalizedQuery),
      ),
    [recentViews, normalizedQuery],
  );

  const counts: Record<SavedTab, number> = {
    properties: records.filter(
      (item) => item.kind === "property",
    ).length,

    projects: records.filter(
      (item) => item.kind === "project",
    ).length,

    localities: records.filter(
      (item) => item.kind === "locality",
    ).length,

    searches: searches.length,
    recent: recentViews.length,
  };

  const statusCopy: Record<PersistenceStatus, string> = {
    connected:
      "Account sync connected — reported by the host application.",

    "session-only":
      "Session only — this collection is not saved to your account.",

    "not-connected":
      "Account sync is not connected. This view does not claim persistent storage.",
  };

  return (
    <main className={styles.experience}>
      <div
        className={styles.ambient}
        aria-hidden="true"
      />

      <div className={styles.inner}>
        <header className={styles.hero}>
          <div>
            <p className={styles.eyebrow}>
              <span
                className={styles.eyebrowDot}
                aria-hidden="true"
              />
              YOUR DECISION SPACE
            </p>

            <h1>
              Saved, <em>with intent.</em>
            </h1>

            <p className={styles.heroText}>
              Bring your shortlist into focus. Keep promising
              places close and return to their supplied details.
            </p>
          </div>

          <div
            className={styles.heroMetric}
            aria-label={
              `${records.length + searches.length} saved items`
            }
          >
            <span className={styles.metricLabel}>
              YOUR COLLECTION
            </span>

            <strong>
              {String(
                records.length + searches.length,
              ).padStart(2, "0")}
            </strong>

            <span className={styles.metricFoot}>
              supplied items
            </span>
          </div>
        </header>

        <div
          className={styles.syncNotice}
          role="status"
        >
          <span
            className={styles.syncPulse}
            aria-hidden="true"
          />
          <span>{statusCopy[persistenceStatus]}</span>
        </div>

        <section
          className={styles.workspace}
          aria-label="Saved items workspace"
        >
          <div className={styles.workspaceHead}>
            <div>
              <p className={styles.eyebrow}>
                COLLECTIONS
              </p>

              <h2>Your shortlist, organized.</h2>
            </div>

            <label className={styles.searchBox}>
              <span aria-hidden="true">⌕</span>

              <span className={styles.srOnly}>
                Search saved items
              </span>

              <input
                value={query}
                onChange={(event) =>
                  setQuery(event.target.value)
                }
                placeholder="Find something…"
              />
            </label>
          </div>

          <div
            className={styles.tabs}
            role="tablist"
            aria-label="Saved item categories"
          >
            {TABS.map((tab) => (
              <button
                key={tab.id}
                type="button"
                role="tab"
                aria-selected={activeTab === tab.id}
                className={
                  `${styles.tab} ${
                    activeTab === tab.id
                      ? styles.activeTab
                      : ""
                  }`
                }
                onClick={() => setActiveTab(tab.id)}
              >
                {tab.label}
                <span>{counts[tab.id]}</span>
              </button>
            ))}
          </div>

          <div
            className={styles.tabPanel}
            role="tabpanel"
          >
            {activeTab === "properties" ? (
              <SavedProperties
                items={visibleRecords}
                onRemove={
                  onRemoveRecord
                    ? (id) =>
                        onRemoveRecord(id, "property")
                    : undefined
                }
              />
            ) : null}

            {activeTab === "projects" ? (
              <SavedProjects
                items={visibleRecords}
                onRemove={
                  onRemoveRecord
                    ? (id) =>
                        onRemoveRecord(id, "project")
                    : undefined
                }
              />
            ) : null}

            {activeTab === "localities" ? (
              <SavedLocalities
                items={visibleRecords}
                onRemove={
                  onRemoveRecord
                    ? (id) =>
                        onRemoveRecord(id, "locality")
                    : undefined
                }
              />
            ) : null}

            {activeTab === "searches" ? (
              <SavedSearches
                items={visibleSearches}
                onRemove={onRemoveSearch}
              />
            ) : null}

            {activeTab === "recent" ? (
              <RecentViews items={visibleRecent} />
            ) : null}
          </div>
        </section>
      </div>
    </main>
  );
}
