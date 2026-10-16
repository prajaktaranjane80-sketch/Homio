
export type HomioConversionEventName =
  | "enquiry_started"
  | "enquiry_submitted"
  | "visit_requested"
  | "visit_confirmed"
  | "post_property_started"
  | "post_property_submitted"
  | "professional_signup_started"
  | "professional_signup_completed"
  | "deal_stage_viewed";

export interface HomioConversionEvent {
  name: HomioConversionEventName;
  occurredAt?: string;
  source?:
    | "property"
    | "project"
    | "search"
    | "content"
    | "navigation"
    | "account"
    | "unknown";
  entityType?: "property" | "project" | "market" | "none";
  entityId?: string;
  marketCode?: string;
}

export type HomioConversionSink = (
  event: HomioConversionEvent,
) => void;

const EVENT_NAMES = new Set<HomioConversionEventName>([
  "enquiry_started",
  "enquiry_submitted",
  "visit_requested",
  "visit_confirmed",
  "post_property_started",
  "post_property_submitted",
  "professional_signup_started",
  "professional_signup_completed",
  "deal_stage_viewed",
]);

const SOURCES = new Set([
  "property",
  "project",
  "search",
  "content",
  "navigation",
  "account",
  "unknown",
]);

const ENTITY_TYPES = new Set([
  "property",
  "project",
  "market",
  "none",
]);

const SAFE_ID = /^[a-zA-Z0-9_-]{1,80}$/;
const SAFE_MARKET_CODE = /^[A-Z]{2,3}(?:-[A-Z0-9]{2,8})?$/;

export function sanitizeConversionEvent(
  event: HomioConversionEvent,
): HomioConversionEvent | null {
  if (!event || !EVENT_NAMES.has(event.name)) {
    return null;
  }

  const occurredAt =
    typeof event.occurredAt === "string" &&
    Number.isFinite(Date.parse(event.occurredAt))
      ? event.occurredAt
      : undefined;

  const source =
    typeof event.source === "string" &&
    SOURCES.has(event.source)
      ? event.source
      : undefined;

  const entityType =
    typeof event.entityType === "string" &&
    ENTITY_TYPES.has(event.entityType)
      ? event.entityType
      : undefined;

  return {
    name: event.name,
    ...(occurredAt ? { occurredAt } : {}),
    ...(source
      ? { source: source as HomioConversionEvent["source"] }
      : {}),
    ...(entityType
      ? { entityType: entityType as HomioConversionEvent["entityType"] }
      : {}),
    ...(typeof event.entityId === "string" &&
    SAFE_ID.test(event.entityId)
      ? { entityId: event.entityId }
      : {}),
    ...(typeof event.marketCode === "string" &&
    SAFE_MARKET_CODE.test(event.marketCode)
      ? { marketCode: event.marketCode }
      : {}),
  };
}

export function emitConversionEvent(
  sink: HomioConversionSink | undefined,
  event: HomioConversionEvent,
): void {
  if (!sink) return;

  try {
    const safeEvent = sanitizeConversionEvent(event);

    if (safeEvent) {
      sink(safeEvent);
    }
  } catch {
    // Conversion tracking must never block a user task.
  }
}
