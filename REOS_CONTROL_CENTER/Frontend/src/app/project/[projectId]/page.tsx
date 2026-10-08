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

  return {
    title: `${project.name} | HOMIO`,
    description:
      `${project.kindLabel} in ${project.location}. ` +
      `${project.configurations.join(", ")}. ` +
      "Explore the project experience on HOMIO.",
    alternates: {
      canonical: `/project/${project.id}`,
    },
    openGraph: {
      title: `${project.name} | HOMIO`,
      description:
        `${project.kindLabel} in ${project.location}. ` +
        "Explore the project experience on HOMIO.",
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
