
import ProLeads from "@/features/f11_professional/ProLeads";
import ProShell from "@/features/f11_professional/ProShell";
import { requireSignedInProPreview } from "@/features/f11_professional/pro-server";

export const metadata = {
  title: "HOMIO Pro | Leads",
  robots: { index: false, follow: false },
};

export const dynamic = "force-dynamic";

export default async function ProLeadsPage() {
  const identity = await requireSignedInProPreview("/pro/leads");

  return (
    <ProShell identity={identity} activeSection="leads">
      <ProLeads />
    </ProShell>
  );
}
