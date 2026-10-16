
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

export type HomioAnalyticsPrimitive = string | number | boolean | null;

export interface HomioAnalyticsEvent {
  name: HomioAnalyticsEventName;
  occurredAt?: string;
  properties?: Readonly<Record<string, HomioAnalyticsPrimitive>>;
}

export type HomioAnalyticsSink = (event: HomioAnalyticsEvent) => void;

const SAFE_PROPERTY_KEYS = new Set([
  "source",
  "surface",
  "page_type",
  "result_count",
  "filter_count",
  "sort",
  "entity_type",
  "entity_id",
  "market_code",
  "position",
  "category",
  "listing_type",
  "property_type",
  "device_class",
  "experiment",
]);

function normalizePropertyKey(key: string): string {
  return key
    .replace(/([a-z0-9])([A-Z])/g, "$1_$2")
    .normalize("NFKC")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
}

function isSafePrimitive(
  value: unknown,
): value is HomioAnalyticsPrimitive {
  return (
    value === null ||
    typeof value === "boolean" ||
    (typeof value === "number" && Number.isFinite(value)) ||
    (typeof value === "string" && value.length <= 80)
  );
}

export function sanitizeAnalyticsEvent(
  event: HomioAnalyticsEvent,
): HomioAnalyticsEvent {
  const properties: Record<string, HomioAnalyticsPrimitive> = {};

  for (const [rawKey, value] of Object.entries(event.properties ?? {})) {
    const key = normalizePropertyKey(rawKey);

    // Default-deny: only explicitly approved analytics dimensions pass.
    if (!SAFE_PROPERTY_KEYS.has(key)) continue;
    if (!isSafePrimitive(value)) continue;

    if (["result_count", "filter_count", "position"].includes(key)) {
      if (typeof value !== "number" || value < 0) continue;
    }

    if (
      key === "market_code" &&
      typeof value === "string" &&
      !/^[A-Z]{2,3}(?:-[A-Z0-9]{2,8})?$/.test(value)
    ) {
      continue;
    }

    if (
      key === "entity_id" &&
      typeof value === "string" &&
      !/^[a-zA-Z0-9_-]{1,80}$/.test(value)
    ) {
      continue;
    }

    properties[key] = value;
  }

  const occurredAt =
    typeof event.occurredAt === "string" &&
    Number.isFinite(Date.parse(event.occurredAt))
      ? event.occurredAt
      : undefined;

  return {
    name: event.name,
    ...(occurredAt ? { occurredAt } : {}),
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
