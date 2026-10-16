
import ProDeals from "@/features/f11_professional/ProDeals";
import ProShell from "@/features/f11_professional/ProShell";
import { requireSignedInProPreview } from "@/features/f11_professional/pro-server";

export const metadata = {
  title: "HOMIO Pro | Deals",
  robots: { index: false, follow: false },
};

export const dynamic = "force-dynamic";

export default async function ProDealsPage() {
  const identity = await requireSignedInProPreview("/pro/deals");

  return (
    <ProShell identity={identity} activeSection="deals">
      <ProDeals />
    </ProShell>
  );
}
