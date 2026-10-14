import type {
  SearchCurrency,
  SearchIntent,
} from "@/features/f03_search/search.types";

import type { AIPromptSuggestion } from "./ai.types";

/**
 * Keep false until an approved server-side AI service is connected.
 * Do not change this flag just to alter the visual status.
 */
export const AI_LIVE_SERVICE_CONNECTED = false;

export const AI_INTENT_OPTIONS: ReadonlyArray<{
  value: SearchIntent;
  label: string;
}> = [
  { value: "buy", label: "Buy a home" },
  { value: "rent", label: "Find a rental" },
  { value: "commercial", label: "Commercial space" },
  { value: "projects", label: "Explore projects" },
  { value: "land", label: "Land and plots" },
];

export const AI_CURRENCY_OPTIONS: ReadonlyArray<{
  value: SearchCurrency;
  label: string;
}> = [
  { value: "INR", label: "INR · ₹" },
  { value: "AED", label: "AED" },
  { value: "SGD", label: "SGD" },
  { value: "JPY", label: "JPY · ¥" },
];

export const AI_PROMPT_SUGGESTIONS: readonly AIPromptSuggestion[] = [
  {
    id: "first-home",
    title: "Plan a first home",
    description: "Turn your priorities into a clear property brief.",
    prompt:
      "Help me define a first-home brief with location, space, budget and essential features.",
    intent: "buy",
    glyph: "⌂",
  },
  {
    id: "rental",
    title: "Find a better rental",
    description: "Clarify commute, lease needs and monthly costs.",
    prompt:
      "Help me prepare a rental brief covering area, monthly budget, commute, lease and move-in needs.",
    intent: "rent",
    glyph: "↗",
  },
  {
    id: "commercial",
    title: "Plan a workspace",
    description: "Outline size, access, use and operating needs.",
    prompt:
      "Help me define a commercial property brief for location, usable area, access and budget.",
    intent: "commercial",
    glyph: "▦",
  },
  {
    id: "compare",
    title: "Compare two options",
    description: "Use the same checklist for each property.",
    prompt:
      "Help me compare two properties using total cost, location, condition, documents and suitability.",
    intent: "buy",
    glyph: "⇄",
  },
];

export const AI_DECISION_PRINCIPLES = [
  {
    title: "Total cost, not just price",
    detail:
      "Check recurring charges, taxes, fees and financing with the relevant local professionals.",
  },
  {
    title: "Location fit",
    detail:
      "Compare transport, daily services and commute against your actual priorities.",
  },
  {
    title: "Evidence before confidence",
    detail:
      "Verify listing details, ownership, approvals and availability with authoritative sources.",
  },
] as const;

/**
 * Creates a link using the query-parameter conventions of existing F03 Search.
 * No result or property facts are generated here.
 */
export function buildSearchHref(input: {
  intent: SearchIntent;
  location: string;
  budget: string;
  currency: SearchCurrency;
  query: string;
}): string {
  const params = new URLSearchParams();

  params.set("intent", input.intent);

  const location = input.location.trim();
  const budget = input.budget.trim();
  const query = input.query.trim();

  if (location) {
    params.set("city", location);
  }

  if (budget) {
    params.set("maxBudget", budget);
    params.set("budgetCurrency", input.currency);
  }

  if (query) {
    params.set("q", query);
  }

  return `/search?${params.toString()}`;
}
