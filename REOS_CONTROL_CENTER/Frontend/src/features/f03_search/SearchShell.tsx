"use client";

import { useEffect, useMemo, useState } from "react";

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

export default function SearchShell() {
  const [state, setState] = useState<SearchState>(
    createDefaultSearchState(),
  );

  const [filterOpen, setFilterOpen] = useState(false);
  const [draftFilters, setDraftFilters] = useState<SearchFilters>(
    createEmptySearchFilters(),
  );

  const [urlInitialized, setUrlInitialized] = useState(false);
  const [savedIds, setSavedIds] = useState<string[]>([]);
  const [comparedIds, setComparedIds] = useState<string[]>([]);
  const [selectedId, setSelectedId] = useState<string>();

  useEffect(() => {
    function hydrateFromUrl() {
      const params = new URLSearchParams(window.location.search);
      const incoming = normalizeIncomingState(
        searchStateFromParams(params),
      );

      // URL hydration is intentional when mounting or navigating history.
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
    if (result.entityType !== "property") {
      return;
    }

    setSavedIds((current) =>
      current.includes(result.id)
        ? current.filter((id) => id !== result.id)
        : [...current, result.id],
    );
  }

  function toggleCompared(result: SearchResultCardData) {
    if (result.entityType !== "property") {
      return;
    }

    setComparedIds((current) => {
      if (current.includes(result.id)) {
        return current.filter((id) => id !== result.id);
      }

      if (current.length >= 3) {
        return current;
      }

      return [...current, result.id];
    });
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
              <span
                style={{
                  color: "#667085",
                  fontSize: 12,
                }}
              >
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
            onSelect={(result) => setSelectedId(result.id)}
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
          <span>
            HOMIO experience preview · Not authoritative inventory
          </span>

          <span>
            {state.intent === "projects"
              ? "Project discovery · Account persistence not connected"
              : state.viewMode === "map"
                ? "Geographic map unavailable until authoritative coordinates exist"
                : "Save and compare states are temporary to this page session"}
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
