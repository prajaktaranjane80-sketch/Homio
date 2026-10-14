import type { SearchResultCardData } from "@/features/f03_search/SearchResultCard";
import type { PropertyRecord } from "@/features/f04_property/property.types";
import type { ProjectRecord } from "@/features/f05_project/project.types";

import type { CompareItem } from "./compare.types";
import type { SavedRecord } from "./saved.types";

export function savedFromSearchResult(
  result: SearchResultCardData,
): SavedRecord {
  const isProject = result.entityType === "project";

  return {
    id: result.id,
    kind: isProject ? "project" : "property",
    title: result.title,
    href: result.href,
    subtitle: result.location,
    statusLabel: result.status,
    detailLine: [
      result.price,
      result.area,
    ].filter(Boolean).join(" · "),
  };
}

export function compareFromSearchResult(
  result: SearchResultCardData,
): CompareItem {
  const isProject = result.entityType === "project";

  return {
    id: result.id,
    kind: isProject ? "project" : "property",
    title: result.title,
    href: result.href,
    subtitle: result.location,
    statusLabel: result.status,
    summary: result.propertyType,
    fields: [
      { label: "Type", value: result.propertyType, group: "overview" },
      { label: "Price", value: result.price || null, group: "pricing" },
      { label: "Area", value: result.area || null, group: "overview" },
      { label: "Location", value: result.location, group: "location" },
      { label: "Bedrooms", value: result.bedrooms ?? null, group: "features" },
      { label: "Bathrooms", value: result.bathrooms ?? null, group: "features" },
      { label: "Status", value: result.status || null, group: "trust" },
      {
        label: "Verification",
        value: result.verified === undefined
          ? null
          : result.verified ? "Source marked verified" : "Not verified",
        group: "trust",
      },
    ],
  };
}

export function savedFromProperty(
  property: PropertyRecord,
): SavedRecord {
  return {
    id: property.id,
    kind: "property",
    title: property.title,
    href: `/property/${encodeURIComponent(property.id)}`,
    subtitle: property.location,
    statusLabel: property.status,
    detailLine: [property.price, property.area]
      .filter(Boolean)
      .join(" · "),
  };
}

export function compareFromProperty(
  property: PropertyRecord,
): CompareItem {
  return {
    id: property.id,
    kind: "property",
    title: property.title,
    href: `/property/${encodeURIComponent(property.id)}`,
    subtitle: property.location,
    statusLabel: property.status,
    fields: [
      { label: "Type", value: property.propertyType, group: "overview" },
      { label: "Price", value: property.price || null, group: "pricing" },
      { label: "Area", value: property.area || null, group: "overview" },
      { label: "Location", value: property.location, group: "location" },
      { label: "Bedrooms", value: property.bedrooms ?? null, group: "features" },
      { label: "Bathrooms", value: property.bathrooms ?? null, group: "features" },
      { label: "Parking", value: property.parking || null, group: "features" },
      { label: "Furnishing", value: property.furnishing || null, group: "features" },
      { label: "Possession", value: property.possession || null, group: "trust" },
      {
        label: "Verification",
        value: property.verified
          ? property.verificationLabel || "Source marked verified"
          : "Not verified",
        group: "trust",
      },
    ],
  };
}

export function savedFromProject(
  project: ProjectRecord,
): SavedRecord {
  return {
    id: project.id,
    kind: "project",
    title: project.name,
    href: `/project/${encodeURIComponent(project.id)}`,
    subtitle: project.location,
    statusLabel: project.status,
    detailLine: [project.priceFrom, project.areaRange]
      .filter(Boolean)
      .join(" · "),
  };
}

export function compareFromProject(
  project: ProjectRecord,
): CompareItem {
  return {
    id: project.id,
    kind: "project",
    title: project.name,
    href: `/project/${encodeURIComponent(project.id)}`,
    subtitle: project.location,
    statusLabel: project.status,
    summary: project.kindLabel,
    fields: [
      { label: "Type", value: project.kindLabel, group: "overview" },
      { label: "Developer", value: project.developerName || null, group: "overview" },
      { label: "Price from", value: project.priceFrom || null, group: "pricing" },
      { label: "Area range", value: project.areaRange || null, group: "overview" },
      { label: "Location", value: project.location, group: "location" },
      { label: "Configurations", value: project.configurations.join(", ") || null, group: "features" },
      { label: "Possession", value: project.possession || null, group: "trust" },
      {
        label: "Verification",
        value: project.verified
          ? project.verificationLabel || "Source marked verified"
          : "Not verified",
        group: "trust",
      },
    ],
  };
}
