export type EmptyStateKind =
  | "no-results"
  | "no-saved-items"
  | "no-comparisons"
  | "no-enquiries"
  | "no-visits"
  | "unavailable"
  | "not-activated";

export interface EmptyStateCopy {
  title: string;
  description: string;
  actionLabel?: string;
  actionHref?: string;
  tone: "neutral" | "notice";
}

export const EMPTY_STATE_POLICY: Record<
  EmptyStateKind,
  EmptyStateCopy
> = {
  "no-results": {
    title: "No matching properties yet",
    description:
      "Try a broader location or remove one or two filters to see more options.",
    actionLabel: "Clear filters",
    tone: "neutral",
  },

  "no-saved-items": {
    title: "Your shortlist starts here",
    description:
      "Save homes or projects you like and they will be collected here.",
    actionLabel: "Explore properties",
    actionHref: "/search",
    tone: "neutral",
  },

  "no-comparisons": {
    title: "Compare with confidence",
    description:
      "Add two or more properties to compare their key details side by side.",
    actionLabel: "Explore properties",
    actionHref: "/search",
    tone: "neutral",
  },

  "no-enquiries": {
    title: "No enquiries yet",
    description:
      "When you contact HOMIO about a property, your enquiry status will appear here.",
    tone: "neutral",
  },

  "no-visits": {
    title: "No visits scheduled",
    description:
      "Request a property visit to keep its coordination details together.",
    tone: "neutral",
  },

  unavailable: {
    title: "This experience is temporarily unavailable",
    description:
      "Please try again shortly. Availability can change independently from the route.",
    actionLabel: "Try again",
    tone: "notice",
  },

  "not-activated": {
    title: "This market is not active yet",
    description:
      "The route is available, but local inventory and operations have not been activated.",
    tone: "notice",
  },
};

export function getEmptyStateCopy(
  kind: EmptyStateKind,
): EmptyStateCopy {
  return EMPTY_STATE_POLICY[kind];
}
