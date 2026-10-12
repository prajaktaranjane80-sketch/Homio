import { getPropertyPreview } from "./property.data";
import type { PropertyRecord } from "./property.types";

const PROPERTY_PREVIEW_IDS = [
  "skyline-residence",
  "central-park-residence",
  "harbour-view-home",
  "modern-city-residence",
  "parkside-family-home",
  "prime-urban-apartment",
  "palm-view-residence",
  "central-garden-residence",
  "prime-metropolitan-home",
  "pune-kalyani-nagar-001",
  "pune-koregaon-park-002",
  "pune-baner-003",
  "pune-viman-nagar-004",
  "pune-wakad-005",
  "pune-hinjewadi-006",
  "pune-magarpattacity-007",
  "pune-aundh-008",
  "furnished-city-apartment",
  "marina-lifestyle-home",
  "central-singapore-residence",
] as const;

/**
 * Returns independent preview records through the existing F04 data adapter.
 * This is a preview catalogue, not authoritative or verified inventory.
 */
export function getAllPropertyPreviews(): PropertyRecord[] {
  return PROPERTY_PREVIEW_IDS
    .map((id) => getPropertyPreview(id))
    .filter((record): record is PropertyRecord => record !== null);
}
