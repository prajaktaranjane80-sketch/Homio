import type { Metadata } from "next";
import { notFound } from "next/navigation";

import EnquiryShell, {
  type EnquiryWorkspaceMode,
} from "@/features/f09_enquiry_visit/EnquiryShell";
import type { EnquiryTarget } from "@/features/f09_enquiry_visit/enquiry.types";
import { getPropertyPreview } from "@/features/f04_property/property.data";
import { getProjectPreview } from "@/features/f05_project/project.data";

type SearchParam = string | string[] | undefined;

type EnquiryRouteProps = Readonly<{
  searchParams: Promise<{
    kind?: SearchParam;
    id?: SearchParam;
    mode?: SearchParam;
  }>;
}>;

export const metadata: Metadata = {
  title: "Contact HOMIO | Enquiry Preview",
  description:
    "Prepare a property-related question or general enquiry in the HOMIO experience preview.",
  robots: {
    index: false,
    follow: true,
  },
};

const GENERAL_ENQUIRY_TARGET: EnquiryTarget = {
  kind: "general",
  title: "General HOMIO enquiry",
};

function firstParam(value: SearchParam): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

export default async function EnquiryRoute({
  searchParams,
}: EnquiryRouteProps) {
  const query = await searchParams;

  const kind = firstParam(query.kind);
  const id = firstParam(query.id);
  const requestedMode = firstParam(query.mode);

  let target: EnquiryTarget = GENERAL_ENQUIRY_TARGET;

  if (kind === "property") {
    if (!id) notFound();

    const property = getPropertyPreview(id);

    if (!property) notFound();

    target = {
      kind: "property",
      id: property.id,
      title: property.shortTitle,
      location: property.location,
      href: `/property/${encodeURIComponent(property.id)}`,
    };
  } else if (kind === "project") {
    if (!id) notFound();

    const project = getProjectPreview(id);

    if (!project) notFound();

    target = {
      kind: "project",
      id: project.id,
      title: project.name,
      location: project.location,
      href: `/project/${encodeURIComponent(project.id)}`,
    };
  } else if (kind && kind !== "general") {
    notFound();
  }

  const initialMode: EnquiryWorkspaceMode =
    requestedMode === "visit" && target.kind !== "general"
      ? "visit"
      : "enquiry";

  const workspaceKey =
    target.kind + ":" + (target.id ?? "general") + ":" + initialMode;

  return (
    <EnquiryShell
      key={workspaceKey}
      target={target}
      initialMode={initialMode}
    />
  );
}
