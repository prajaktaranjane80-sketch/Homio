"use client";

import { useEffect } from "react";
import CompareShell from "@/features/f06_save_compare/CompareShell";
import {
  compareFromProperty,
  compareFromProject,
} from "@/features/f06_save_compare/saveCompareAdapters";
import {
  clearComparedItems,
  removeComparedItem,
  replaceComparedItems,
  useSaveCompareSession,
} from "@/features/f06_save_compare/saveCompareSession";
import { getPropertyPreview } from "@/features/f04_property/property.data";
import { getProjectPreview } from "@/features/f05_project/project.data";
import type { CompareItem } from "@/features/f06_save_compare/compare.types";

type SharedCompareReference = Readonly<{
  kind: "property" | "project";
  id: string;
}>;

function isSharedCompareReference(value: unknown): value is SharedCompareReference {
  if (typeof value !== "object" || value === null) return false;
  const candidate = value as { kind?: unknown; id?: unknown };
  return (
    (candidate.kind === "property" || candidate.kind === "project") &&
    typeof candidate.id === "string" &&
    candidate.id.trim().length > 0
  );
}

function parseSharedReferences(raw: string): SharedCompareReference[] {
  try {
    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(isSharedCompareReference).slice(0, 4);
  } catch {
    return [];
  }
}

function resolveReference(reference: SharedCompareReference): CompareItem | null {
  if (reference.kind === "property") {
    const property = getPropertyPreview(reference.id);
    return property ? compareFromProperty(property) : null;
  }

  const project = getProjectPreview(reference.id);
  return project ? compareFromProject(project) : null;
}

export default function ComparePage() {
  const { comparedItems } = useSaveCompareSession();

  useEffect(() => {
    const url = new URL(window.location.href);
    const raw = url.searchParams.get("compare");
    if (raw === null) return;

    const resolved = parseSharedReferences(raw)
      .map(resolveReference)
      .filter((item): item is CompareItem => item !== null);

    if (resolved.length > 0) {
      replaceComparedItems(resolved);
    }

    // Avoid re-applying the share payload if the user clears the comparison and reloads.
    url.searchParams.delete("compare");
    const query = url.searchParams.toString();
    const nextUrl = `${url.pathname}${query ? `?${query}` : ""}${url.hash}`;
    window.history.replaceState(window.history.state, "", nextUrl);
  }, []);

  return (
    <CompareShell
      items={comparedItems}
      onRemove={(id, kind) => removeComparedItem(id, kind)}
      onClear={clearComparedItems}
    />
  );
}
