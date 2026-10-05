"use client";

import { useEffect, useMemo, useState } from "react";
import SearchActions from "@/features/f03_search/SearchActions";
import SearchFilterDrawer from "@/features/f03_search/SearchFilterDrawer";
import SearchHeader from "@/features/f03_search/SearchHeader";
import SearchLoadingState from "@/features/f03_search/SearchLoadingState";
import SearchResultCount from "@/features/f03_search/SearchResultCount";
import SearchResults from "@/features/f03_search/SearchResults";
import SearchSortBar from "@/features/f03_search/SearchSortBar";
import SearchSummary from "@/features/f03_search/SearchSummary";
import SearchViewToggle from "@/features/f03_search/SearchViewToggle";
import type { SearchResultCardData } from "@/features/f03_search/SearchResultCard";
import type { SearchState } from "@/features/f03_search/search.types";
import {
  createDefaultSearchState,
  countActiveFilters,
  searchStateFromParams,
} from "@/features/f03_search/search.utils";
import styles from "./page.module.css";

const PAGE_SIZE = 8;

const SAMPLE_RESULTS: SearchResultCardData[] = [
  {
    id: "pune-kalyani-nagar-001",
    title: "Contemporary 3 BHK Residence",
    location: "Kalyani Nagar, Pune",
    propertyType: "Apartment",
    price: "₹2.35 Cr",
    area: "1,850 sq.ft.",
    bedrooms: 3,
    bathrooms: 3,
    image:
      "https://images.unsplash.com/photo-1600607687920-4e2a09cf159d?auto=format&fit=crop&w=1200&q=80",
    verified: true,
    projectName: "HOMIO Kalyani Residences",
    status: "Ready to move",
    href: "/property/pune-kalyani-nagar-001",
  },
  {
    id: "pune-koregaon-park-002",
    title: "Refined 4 BHK Urban Villa",
    location: "Koregaon Park, Pune",
    propertyType: "Villa",
    price: "₹4.80 Cr",
    area: "3,200 sq.ft.",
    bedrooms: 4,
    bathrooms: 4,
    image:
      "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=80",
    verified: true,
    projectName: "Parkside Villas",
    status: "New launch",
    href: "/property/pune-koregaon-park-002",
  },
  {
    id: "pune-baner-003",
    title: "Modern 2 BHK City Home",
    location: "Baner, Pune",
    propertyType: "Apartment",
    price: "₹1.28 Cr",
    area: "1,220 sq.ft.",
    bedrooms: 2,
    bathrooms: 2,
    image:
      "https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea?auto=format&fit=crop&w=1200&q=80",
    verified: true,
    projectName: "Baner Heights",
    status: "Under construction",
    href: "/property/pune-baner-003",
  },
  {
    id: "pune-viman-nagar-004",
    title: "Premium 3 BHK Residence",
    location: "Viman Nagar, Pune",
    propertyType: "Apartment",
    price: "₹1.95 Cr",
    area: "1,640 sq.ft.",
    bedrooms: 3,
    bathrooms: 3,
    image:
      "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=1200&q=80",
    verified: true,
    projectName: "Skyline Viman",
    status: "Ready to move",
    href: "/property/pune-viman-nagar-004",
  },
  {
    id: "pune-wakad-005",
    title: "Family 3 BHK Smart Home",
    location: "Wakad, Pune",
    propertyType: "Apartment",
    price: "₹1.12 Cr",
    area: "1,470 sq.ft.",
    bedrooms: 3,
    bathrooms: 2,
    image:
      "https://images.unsplash.com/photo-1600607688969-a5bfcd646154?auto=format&fit=crop&w=1200&q=80",
    verified: true,
    projectName: "Westline Homes",
    status: "New launch",
    href: "/property/pune-wakad-005",
  },
  {
    id: "pune-hinjewadi-006",
    title: "Connected 2 BHK Investment Home",
    location: "Hinjewadi, Pune",
    propertyType: "Apartment",
    price: "₹89 Lakh",
    area: "1,060 sq.ft.",
    bedrooms: 2,
    bathrooms: 2,
    image:
      "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?auto=format&fit=crop&w=1200&q=80",
    verified: true,
    projectName: "Hinjewadi Central",
    status: "Under construction",
    href: "/property/pune-hinjewadi-006",
  },
  {
    id: "pune-magarpattacity-007",
    title: "Executive 3 BHK Residence",
    location: "Magarpatta City, Pune",
    propertyType: "Apartment",
    price: "₹1.72 Cr",
    area: "1,580 sq.ft.",
    bedrooms: 3,
    bathrooms: 3,
    image:
      "https://images.unsplash.com/photo-1600607687920-4e2a09cf159d?auto=format&fit=crop&w=1200&q=80",
    verified: true,
    projectName: "City Park Residences",
    status: "Ready to move",
    href: "/property/pune-magarpattacity-007",
  },
  {
    id: "pune-aundh-008",
    title: "Elegant 4 BHK Residence",
    location: "Aundh, Pune",
    propertyType: "Apartment",
    price: "₹2.85 Cr",
    area: "2,250 sq.ft.",
    bedrooms: 4,
    bathrooms: 4,
    image:
      "https://images.unsplash.com/photo-1600585152915-d208bec867a1?auto=format&fit=crop&w=1200&q=80",
    verified: true,
    projectName: "Aundh Grand",
    status: "Ready to move",
    href: "/property/pune-aundh-008",
  },
];

export default function SearchPage() {
  const [state, setState] = useState<SearchState>(
    createDefaultSearchState(),
  );
  const [filterOpen, setFilterOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [savedIds, setSavedIds] = useState<string[]>([]);
  const [comparedIds, setComparedIds] = useState<string[]>([]);
  const [selectedId, setSelectedId] = useState<string>();

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    setState(searchStateFromParams(params));
  }, []);

  const filteredResults = useMemo(() => {
    let results = [...SAMPLE_RESULTS];

    const propertyTypes = state.filters.propertyTypes;

    if (propertyTypes.length > 0) {
      results = results.filter((item) =>
        propertyTypes.includes(item.propertyType),
      );
    }

    if (state.filters.bedrooms.length > 0) {
      results = results.filter(
        (item) =>
          item.bedrooms !== undefined &&
          state.filters.bedrooms.includes(item.bedrooms),
      );
    }

    if (state.filters.verifiedOnly) {
      results = results.filter((item) => item.verified);
    }

    if (state.filters.propertyStatus.length > 0) {
      results = results.filter(
        (item) =>
          item.status &&
          state.filters.propertyStatus.includes(item.status),
      );
    }

    if (state.location?.locality || state.location?.city) {
      const query = (
        state.location.locality ??
        state.location.city ??
        ""
      ).toLowerCase();

      if (query) {
        results = results.filter((item) =>
          item.location.toLowerCase().includes(query),
        );
      }
    }

    if (state.query) {
      const query = state.query.toLowerCase();

      results = results.filter((item) =>
        `${item.title} ${item.location} ${item.projectName ?? ""}`
          .toLowerCase()
          .includes(query),
      );
    }

    return results;
  }, [state]);

  const totalPages = Math.max(
    1,
    Math.ceil(filteredResults.length / PAGE_SIZE),
  );

  const visibleResults = filteredResults.slice(
    (state.page - 1) * PAGE_SIZE,
    state.page * PAGE_SIZE,
  );

  const activeFilters = countActiveFilters(state.filters);

  function updateState(next: SearchState) {
    setState({
      ...next,
      page: Math.min(next.page, totalPages),
    });
  }

  function toggleSaved(property: SearchResultCardData) {
    setSavedIds((current) =>
      current.includes(property.id)
        ? current.filter((id) => id !== property.id)
        : [...current, property.id],
    );
  }

  function toggleCompared(property: SearchResultCardData) {
    setComparedIds((current) =>
      current.includes(property.id)
        ? current.filter((id) => id !== property.id)
        : current.length >= 3
          ? current
          : [...current, property.id],
    );
  }

  function changeSort(nextSort: SearchState["sort"]) {
    setState((current) => ({
      ...current,
      sort: nextSort,
      page: 1,
    }));
  }

  function changeView(nextView: SearchState["viewMode"]) {
    setState((current) => ({
      ...current,
      viewMode: nextView,
    }));
  }

  function changePage(nextPage: number) {
    setState((current) => ({
      ...current,
      page: Math.max(1, Math.min(nextPage, totalPages)),
    }));

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  }

  return (
    <main className={styles.page}>
      <div className="homio-container">
        <SearchHeader
          title="Search HOMIO properties."
          description="Discover homes, projects, commercial opportunities and land through a single global property search experience."
        />

        <SearchSummary state={state} />

        <div className={styles.toolbar}>
          <div className={styles.toolbarLeft}>
            <button
              type="button"
              className={styles.filterButton}
              onClick={() => setFilterOpen(true)}
            >
              Filters
              {activeFilters > 0 ? (
                <span className={styles.filterBadge}>{activeFilters}</span>
              ) : null}
            </button>

            <SearchResultCount
              total={filteredResults.length}
              page={state.page}
              pageSize={PAGE_SIZE}
            />
          </div>

          <div className={styles.toolbarRight}>
            <SearchSortBar value={state.sort} onChange={changeSort} />
            <SearchViewToggle
              value={state.viewMode}
              onChange={changeView}
            />
          </div>
        </div>

        <div className={styles.actionsRow}>
          <SearchActions state={state} onChange={updateState} />
        </div>

        {loading ? (
          <SearchLoadingState />
        ) : (
          <SearchResults
            properties={visibleResults}
            viewMode={state.viewMode}
            savedIds={savedIds}
            comparedIds={comparedIds}
            selectedId={selectedId}
            onSave={toggleSaved}
            onCompare={toggleCompared}
            onSelect={(property) => setSelectedId(property.id)}
          />
        )}

        {filteredResults.length === 0 ? (
          <div className={styles.empty}>
            <strong>No properties match this search.</strong>
            <span>
              Adjust the filters or explore another location.
            </span>
          </div>
        ) : null}

        <div className={styles.pageNote}>
          <span>
            HOMIO search foundation • Pune activation path
          </span>
          <span>
            {state.viewMode === "map" ? "Map discovery" : "Property discovery"}
          </span>
        </div>
      </div>

      <SearchFilterDrawer
        open={filterOpen}
        filters={state.filters}
        onChange={(filters) => {
          setLoading(true);
          setState((current) => ({
            ...current,
            filters,
            page: 1,
          }));

          window.setTimeout(() => {
            setLoading(false);
          }, 180);
        }}
        onClose={() => setFilterOpen(false)}
      />
    </main>
  );
}
