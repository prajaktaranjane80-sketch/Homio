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

const SAFE_ID = /^[a-zA-Z0-9_-]{1,80}$/;
const SAFE_MARKET_CODE =
  /^[A-Z]{2,3}(?:-[A-Z0-9]{2,8})?$/;

export function sanitizeConversionEvent(
  event: HomioConversionEvent,
): HomioConversionEvent {
  return {
    name: event.name,
    ...(event.occurredAt
      ? { occurredAt: event.occurredAt }
      : {}),
    ...(event.source ? { source: event.source } : {}),
    ...(event.entityType
      ? { entityType: event.entityType }
      : {}),
    ...(event.entityId && SAFE_ID.test(event.entityId)
      ? { entityId: event.entityId }
      : {}),
    ...(event.marketCode &&
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
    sink(sanitizeConversionEvent(event));
  } catch {
    // Conversion tracking must never block a user task.
  }
}
