export type HomioAnalyticsEventName =
  | "page_view"
  | "search_submitted"
  | "search_filter_changed"
  | "property_opened"
  | "project_opened"
  | "property_saved"
  | "property_unsaved"
  | "comparison_added"
  | "comparison_removed"
  | "market_selector_opened"
  | "content_opened";

export type HomioAnalyticsPrimitive =
  | string
  | number
  | boolean
  | null;

export interface HomioAnalyticsEvent {
  name: HomioAnalyticsEventName;
  occurredAt?: string;
  properties?: Readonly<
    Record<string, HomioAnalyticsPrimitive>
  >;
}

export type HomioAnalyticsSink = (
  event: HomioAnalyticsEvent,
) => void;

const FORBIDDEN_PROPERTY_KEYS = new Set([
  "email",
  "phone",
  "mobile",
  "name",
  "address",
  "message",
  "password",
  "token",
  "document",
  "owner_document",
  "contact_details",
]);

export function sanitizeAnalyticsEvent(
  event: HomioAnalyticsEvent,
): HomioAnalyticsEvent {
  const properties: Record<
    string,
    HomioAnalyticsPrimitive
  > = {};

  for (const [key, value] of Object.entries(
    event.properties ?? {},
  )) {
    const normalizedKey = key
      .toLowerCase()
      .replace(/[\s-]+/g, "_");

    if (FORBIDDEN_PROPERTY_KEYS.has(normalizedKey)) {
      continue;
    }

    if (typeof value === "string" && value.length > 120) {
      continue;
    }

    if (
      value === null ||
      typeof value === "string" ||
      typeof value === "number" ||
      typeof value === "boolean"
    ) {
      properties[key] = value;
    }
  }

  return {
    name: event.name,
    ...(event.occurredAt
      ? { occurredAt: event.occurredAt }
      : {}),
    properties,
  };
}

export function emitAnalyticsEvent(
  sink: HomioAnalyticsSink | undefined,
  event: HomioAnalyticsEvent,
): void {
  if (!sink) return;

  try {
    sink(sanitizeAnalyticsEvent(event));
  } catch {
    // Analytics must never interrupt a user task.
  }
}
