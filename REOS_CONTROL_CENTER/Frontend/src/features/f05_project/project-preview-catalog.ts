import { getProjectPreview } from "./project.data";
import type { ProjectRecord } from "./project.types";

const PROJECT_PREVIEW_IDS = [
  "homio-kalyani-residences-001",
  "pune-east-collection-001",
  "baner-urban-collection-001",
  "aundh-premium-collection-001",
  "harbour-residences",
  "marina-crest",
  "the-meridian",
] as const;

/**
 * Returns existing F05 project previews without duplicating project records.
 * These records do not claim verified project availability.
 */
export function getAllProjectPreviews(): ProjectRecord[] {
  return PROJECT_PREVIEW_IDS
    .map((id) => getProjectPreview(id))
    .filter((record): record is ProjectRecord => record !== null);
}
