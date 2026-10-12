import type { Metadata } from "next";
import { notFound } from "next/navigation";

import ProjectPage from "@/features/f05_project/ProjectPage";
import { getProjectPreview } from "@/features/f05_project/project.data";

type ProjectRouteProps = Readonly<{
  params: Promise<{
    projectId: string;
  }>;
}>;

export async function generateMetadata({
  params,
}: ProjectRouteProps): Promise<Metadata> {
  const { projectId } = await params;
  const project = getProjectPreview(projectId);

  if (!project) {
    return {
      title: "Project unavailable | HOMIO",
      description:
        "This HOMIO project is currently unavailable.",
      robots: {
        index: false,
        follow: false,
      },
    };
  }

  const title =
    `${project.name} | Project Experience Preview | HOMIO`;

  const description =
    `${project.kindLabel} experience preview in ${project.location}. ` +
    "Project facts, pricing, inventory, media and verification " +
    "are not authoritative until confirmed through approved REOS capabilities.";

  return {
    title,
    description,

    // F05 currently serves experience-preview records only.
    // Do not publish them to search indexing or assign a canonical URL.
    robots: {
      index: false,
      follow: true,
    },

    openGraph: {
      title,
      description,
      type: "website",
    },
  };
}

export default async function ProjectRoute({
  params,
}: ProjectRouteProps) {
  const { projectId } = await params;
  const project = getProjectPreview(projectId);

  if (!project) {
    notFound();
  }

  return <ProjectPage project={project} />;
}
