
import ProProjects from "@/features/f11_professional/ProProjects";
import ProShell from "@/features/f11_professional/ProShell";
import { requireSignedInProPreview } from "@/features/f11_professional/pro-server";

export const metadata = {
  title: "HOMIO Pro | Projects",
  robots: { index: false, follow: false },
};

export const dynamic = "force-dynamic";

export default async function ProProjectsPage() {
  const identity = await requireSignedInProPreview("/pro/projects");

  return (
    <ProShell identity={identity} activeSection="projects">
      <ProProjects />
    </ProShell>
  );
}
