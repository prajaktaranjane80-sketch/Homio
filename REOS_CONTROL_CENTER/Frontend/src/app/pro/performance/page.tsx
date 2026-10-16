
import ProPerformance from "@/features/f11_professional/ProPerformance";
import ProShell from "@/features/f11_professional/ProShell";
import { requireSignedInProPreview } from "@/features/f11_professional/pro-server";

export const metadata = {
  title: "HOMIO Pro | Performance",
  robots: { index: false, follow: false },
};

export const dynamic = "force-dynamic";

export default async function ProPerformancePage() {
  const identity = await requireSignedInProPreview("/pro/performance");

  return (
    <ProShell identity={identity} activeSection="performance">
      <ProPerformance />
    </ProShell>
  );
}
