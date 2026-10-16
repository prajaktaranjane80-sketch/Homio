
import ProVisits from "@/features/f11_professional/ProVisits";
import ProShell from "@/features/f11_professional/ProShell";
import { requireSignedInProPreview } from "@/features/f11_professional/pro-server";

export const metadata = {
  title: "HOMIO Pro | Visits",
  robots: { index: false, follow: false },
};

export const dynamic = "force-dynamic";

export default async function ProVisitsPage() {
  const identity = await requireSignedInProPreview("/pro/visits");

  return (
    <ProShell identity={identity} activeSection="visits">
      <ProVisits />
    </ProShell>
  );
}
