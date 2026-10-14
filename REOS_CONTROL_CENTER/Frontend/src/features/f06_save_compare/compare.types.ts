export type CompareEntityKind = "property" | "project" | "locality";

export type CompareFieldGroup =
  | "overview"
  | "pricing"
  | "location"
  | "features"
  | "trust";

export type CompareField = Readonly<{
  /** Stable, human-readable attribute label, e.g. "Bedrooms". */
  label: string;
  value?: string | number | null;
  group: CompareFieldGroup;
}>;

/** Display projection from a source adapter; it is never the canonical property/project record. */
export type CompareItem = Readonly<{
  id: string;
  kind: CompareEntityKind;
  title: string;
  href?: string;
  subtitle?: string;
  statusLabel?: string;
  summary?: string;
  fields: readonly CompareField[];
}>;

export type CompareCategory = "all" | CompareEntityKind;

export const COMPARE_FIELD_GROUPS: ReadonlyArray<{
  id: CompareFieldGroup;
  label: string;
  description: string;
}> = [
  { id: "overview", label: "Overview", description: "Core property or place facts" },
  { id: "pricing", label: "Price & cost", description: "Only source-supplied price information" },
  { id: "location", label: "Location", description: "Area and location context" },
  { id: "features", label: "Features", description: "Configurations, amenities and highlights" },
  { id: "trust", label: "Trust & status", description: "Verification and availability signals when supplied" },
];

export const COMPARE_MAX_ITEMS = 4;
