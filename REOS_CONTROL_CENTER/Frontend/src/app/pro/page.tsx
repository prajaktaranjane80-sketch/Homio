
import ProDashboard from "@/features/f11_professional/ProDashboard";
import ProShell from "@/features/f11_professional/ProShell";
import { requireSignedInProPreview } from "@/features/f11_professional/pro-server";

export const metadata = {
  title: "HOMIO Pro | Professional Command Center",
  robots: { index: false, follow: false },
};

export const dynamic = "force-dynamic";

export default async function ProDashboardPage() {
  const identity = await requireSignedInProPreview("/pro");

  return (
    <ProShell identity={identity} activeSection="dashboard">
      <ProDashboard />
    </ProShell>
  );
}
