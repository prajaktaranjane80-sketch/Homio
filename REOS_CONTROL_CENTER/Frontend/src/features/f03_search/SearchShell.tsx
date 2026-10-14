"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";

import SearchActions from "@/features/f03_search/SearchActions";
import SearchFilterDrawer from "@/features/f03_search/SearchFilterDrawer";
import SearchHeader from "@/features/f03_search/SearchHeader";
import SearchIntentTabs from "@/features/f03_search/SearchIntentTabs";
import SearchLocationField from "@/features/f03_search/SearchLocationField";
import SearchPagination from "@/features/f03_search/SearchPagination";
import SearchResultCount from "@/features/f03_search/SearchResultCount";
import SearchResults from "@/features/f03_search/SearchResults";
import SearchSortBar from "@/features/f03_search/SearchSortBar";
import SearchSummary from "@/features/f03_search/SearchSummary";
import SearchViewToggle from "@/features/f03_search/SearchViewToggle";

import {
  compareFromSearchResult,
  savedFromSearchResult,
} from "@/features/f06_save_compare/saveCompareAdapters";

import {
  toggleComparedItem,
  toggleSavedRecord,
  useSaveCompareSession,
} from "@/features/f06_save_compare/saveCompareSession";

import {
  recordRecentSearch,
  toggleSavedSearch,
  useMyHomioActivity,
} from "@/features/f07_my_homio/myHomioActivityStore";

import {
  SEARCH_DEFAULT_PAGE_SIZE,
  SEARCH_INTENTS,
  SEARCH_INTENT_LABELS,
} from "./search.constants";

import {
  SEARCH_PREVIEW_CATALOG,
  filterSearchCatalog,
} from "./search-preview-catalog";

import type { SearchResultCardData } from "./SearchResultCard";

import type {
  SearchFilters,
  SearchIntent,
  SearchState,
} from "./search.types";

import {
  countActiveFilters,
  createDefaultSearchState,
  createEmptySearchFilters,
  searchStateFromParams,
  searchStateToParams,
} from "./search.utils";

import styles from "./SearchShell.module.css";

const PAGE_SIZE = SEARCH_DEFAULT_PAGE_SIZE;

function normalizeIncomingState(state: SearchState): SearchState {
  if (state.intent !== "projects") {
    return state;
  }

  return {
    ...state,
    filters: createEmptySearchFilters(),
    sort: "relevance",
    viewMode: "list",
    page: 1,
  };
}

function entityIdentity(
  kind: "property" | "project",
  id: string,
): string {
  return `${kind}:${id}`;
}

export default function SearchShell() {
  const [state, setState] = useState<SearchState>(
    createDefaultSearchState(),
  );

  const session = useSaveCompareSession();
  const activity = useMyHomioActivity();

  const [filterOpen, setFilterOpen] = useState(false);

  const [draftFilters, setDraftFilters] = useState<SearchFilters>(
    createEmptySearchFilters(),
  );

  const [urlInitialized, setUrlInitialized] = useState(false);
  const [selectedId, setSelectedId] = useState<string>();

  const filteredResults = useMemo(
    () => filterSearchCatalog(SEARCH_PREVIEW_CATALOG, state),
    [state],
  );

  const totalPages = Math.max(
    1,
    Math.ceil(filteredResults.length / PAGE_SIZE),
  );

  const currentPage = Math.min(
    Math.max(state.page, 1),
    totalPages,
  );

  const visibleResults = filteredResults.slice(
    (currentPage - 1) * PAGE_SIZE,
    currentPage * PAGE_SIZE,
  );

  const activeFilters =
    state.intent === "projects"
      ? 0
      : countActiveFilters(state.filters);

  const entityLabel =
    state.intent === "projects" ? "projects" : "properties";

  const hasNoCatalogueForIntent =
    (state.intent === "commercial" || state.intent === "land") &&
    filteredResults.length === 0;

  const priceSortActive =
    state.sort === "price_low_to_high" ||
    state.sort === "price_high_to_low";

  const searchDraft = useMemo(() => {
    const params = searchStateToParams(state);

    // Pagination does not create a separate saved requirement.
    params.delete("page");

    const queryString = params.toString();
    const href = `/search${queryString ? `?${queryString}` : ""}`;
    const location = state.location?.label.trim();

    const filterDescription =
      state.intent === "projects"
        ? "Project discovery"
        : activeFilters > 0
          ? `${activeFilters} active filter(s)`
          : undefined;

    return {
      href,
      intent: state.intent,
      title: `${SEARCH_INTENT_LABELS[state.intent]}${location ? ` · ${location}` : ""} search`,
      location: location || undefined,
      filtersLabel: filterDescription,
    };
  }, [state, activeFilters]);

  const savedSearch = activity.savedSearches.some(
    (search) => search.href === searchDraft.href,
  );

  const savedIds = useMemo(
    () =>
      session.savedRecords.map((record) =>
        entityIdentity(
          record.kind === "project" ? "project" : "property",
          record.id,
        ),
      ),
    [session.savedRecords],
  );

  const comparedIds = useMemo(
    () =>
      session.comparedItems
        .filter((item) => item.kind === "property" || item.kind === "project")
        .map((item) => entityIdentity(item.kind, item.id)),
    [session.comparedItems],
  );

  useEffect(() => {
    function hydrateFromUrl() {
      const params = new URLSearchParams(window.location.search);

      const incoming = normalizeIncomingState(
        searchStateFromParams(params),
      );

      setState(incoming);
      setDraftFilters(incoming.filters);
      setUrlInitialized(true);
    }

    hydrateFromUrl();

    window.addEventListener("popstate", hydrateFromUrl);

    return () => {
      window.removeEventListener("popstate", hydrateFromUrl);
    };
  }, []);

  useEffect(() => {
    if (!urlInitialized) {
      return;
    }

    const params = searchStateToParams(state);
    const queryString = params.toString();

    const nextUrl =
      `${window.location.pathname}` +
      `${queryString ? `?${queryString}` : ""}` +
      `${window.location.hash}`;

    const currentUrl =
      `${window.location.pathname}` +
      `${window.location.search}` +
      `${window.location.hash}`;

    if (nextUrl !== currentUrl) {
      window.history.replaceState(
        window.history.state,
        "",
        nextUrl,
      );
    }
  }, [state, urlInitialized]);

  useEffect(() => {
    if (urlInitialized) {
      recordRecentSearch(searchDraft);
    }
  }, [searchDraft, urlInitialized]);

  function changeIntent(intent: SearchIntent) {
    setSelectedId(undefined);

    const nextFilters = createEmptySearchFilters();

    setState((current) => ({
      ...current,
      intent,
      filters: nextFilters,
      sort: "relevance",
      viewMode: intent === "projects" ? "list" : current.viewMode,
      page: 1,
    }));

    setDraftFilters(nextFilters);
  }

  function changeLocation(value: string) {
    const normalized = value.trim();

    const location = normalized
      ? {
          label: normalized,
          city: normalized,
        }
      : undefined;

    setState((current) => ({
      ...current,
      location,
      page: 1,
    }));

    setSelectedId(undefined);
  }

  function updateState(next: SearchState) {
    setState({
      ...next,
      page: 1,
    });

    setSelectedId(undefined);
  }

  function toggleSaved(result: SearchResultCardData) {
    toggleSavedRecord(savedFromSearchResult(result));
  }

  function toggleCompared(result: SearchResultCardData) {
    const added = toggleComparedItem(compareFromSearchResult(result));

    if (added) {
      setSelectedId(entityIdentity(result.entityType, result.id));
    }
  }

  function changeSort(nextSort: SearchState["sort"]) {
    setState((current) => ({
      ...current,
      sort: nextSort,
      page: 1,
    }));

    setSelectedId(undefined);
  }

  function changeView(nextView: SearchState["viewMode"]) {
    setState((current) => ({
      ...current,
      viewMode: nextView,
      page: 1,
    }));
  }

  function openFilters() {
    setDraftFilters(state.filters);
    setFilterOpen(true);
  }

  function applyFilters() {
    setState((current) => ({
      ...current,
      filters: draftFilters,
      page: 1,
    }));

    setSelectedId(undefined);
    setFilterOpen(false);
  }

  return (
    <main className={styles.page}>
      <div className="homio-container">
        <SearchHeader
          title="Search HOMIO properties."
          description="Search property and project experience previews. Prices, availability, imagery and verification remain non-authoritative until connected to approved inventory data."
        />

        <div style={{ marginTop: 22, marginBottom: 14 }}>
          <SearchIntentTabs
            intents={SEARCH_INTENTS}
            activeIntent={state.intent}
            onChange={changeIntent}
          />
        </div>

        <div style={{ marginBottom: 18 }}>
          <SearchLocationField
            value={state.location?.label ?? ""}
            onChange={changeLocation}
            intentLabel={SEARCH_INTENT_LABELS[state.intent]}
          />
        </div>

        <SearchSummary state={state} />

        <nav
          aria-label="My HOMIO and discovery actions"
          style={{
            display: "flex",
            flexWrap: "wrap",
            alignItems: "center",
            gap: 10,
            margin: "14px 0",
          }}
        >
          <Link
            href="/my"
            style={shortcutStyle}
          >
            My HOMIO
          </Link>

          <Link
            href="/saved"
            style={shortcutStyle}
          >
            Saved ({session.savedRecords.length})
          </Link>

          <Link
            href="/compare"
            style={shortcutStyle}
          >
            Compare ({session.comparedItems.length}/4)
          </Link>

          <button
            type="button"
            style={{
              ...shortcutStyle,
              cursor: "pointer",
              background: savedSearch ? "#f5ead7" : "#fff",
              borderColor: savedSearch ? "#c59b63" : "#d0c9bc",
            }}
            aria-pressed={savedSearch}
            onClick={() => toggleSavedSearch(searchDraft)}
          >
            {savedSearch ? "✓ Search saved" : "＋ Save this search"}
          </button>

          <span style={{ color: "#777", fontSize: 12 }}>
            Browser-tab activity · Not account-synced
          </span>
        </nav>

        <div className={styles.toolbar}>
          <div className={styles.toolbarLeft}>
            {state.intent !== "projects" ? (
              <button
                type="button"
                className={styles.filterButton}
                onClick={openFilters}
                aria-haspopup="dialog"
                aria-expanded={filterOpen}
              >
                Filters
                {activeFilters > 0 ? (
                  <span className={styles.filterBadge}>
                    {activeFilters}
                  </span>
                ) : null}
              </button>
            ) : null}

            <SearchResultCount
              total={filteredResults.length}
              page={currentPage}
              pageSize={PAGE_SIZE}
              entityLabel={entityLabel}
            />
          </div>

          <div className={styles.toolbarRight}>
            {state.intent !== "projects" ? (
              <>
                <SearchSortBar
                  value={state.sort}
                  onChange={changeSort}
                />

                <SearchViewToggle
                  value={state.viewMode}
                  onChange={changeView}
                />
              </>
            ) : (
              <span style={{ color: "#777", fontSize: 12 }}>
                Project and collection results
              </span>
            )}
          </div>
        </div>

        <div className={styles.actionsRow}>
          <SearchActions
            state={state}
            onChange={updateState}
          />
        </div>

        {filteredResults.length > 0 ? (
          <SearchResults
            properties={visibleResults}
            viewMode={state.viewMode}
            savedIds={savedIds}
            comparedIds={comparedIds}
            selectedId={selectedId}
            onSave={toggleSaved}
            onCompare={toggleCompared}
            onSelect={(result) =>
              setSelectedId(entityIdentity(result.entityType, result.id))
            }
          />
        ) : (
          <div className={styles.empty}>
            <strong>
              {hasNoCatalogueForIntent
                ? `No ${state.intent} preview inventory is connected yet.`
                : state.intent === "projects"
                  ? "No project previews match this search."
                  : "No preview records match this search."}
            </strong>

            <span>
              {hasNoCatalogueForIntent
                ? "HOMIO is not inventing commercial or land listings to fill the gap. Suitable source records are required before those results can be shown."
                : priceSortActive
                  ? `Price sorting is scoped to ${state.filters.budgetCurrency}. Change the budget currency in Filters or choose Relevance.`
                  : "Try another location or clear refinements. Missing price, area, amenity or verification facts are not assumed to be a match."}
            </span>
          </div>
        )}

        {filteredResults.length > 0 ? (
          <SearchPagination
            page={currentPage}
            totalPages={totalPages}
            onChange={(page) =>
              setState((current) => ({
                ...current,
                page,
              }))
            }
          />
        ) : null}

        <div className={styles.pageNote}>
          <span>HOMIO experience preview · Not authoritative inventory</span>
          <span>
            {state.intent === "projects"
              ? "Project discovery · Account persistence not connected"
              : state.viewMode === "map"
                ? "Geographic map unavailable until authoritative coordinates exist"
                : "Save and Compare use the current F06 browser-memory store"}
          </span>
        </div>
      </div>

      <SearchFilterDrawer
        open={filterOpen}
        filters={draftFilters}
        onChange={setDraftFilters}
        onApply={applyFilters}
        onClose={() => setFilterOpen(false)}
      />
    </main>
  );
}

const shortcutStyle: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  gap: 6,
  minHeight: 38,
  padding: "8px 12px",
  border: "1px solid #d0c9bc",
  borderRadius: 999,
  background: "#fff",
  color: "inherit",
  textDecoration: "none",
  fontSize: 12,
  fontWeight: 700,
};
