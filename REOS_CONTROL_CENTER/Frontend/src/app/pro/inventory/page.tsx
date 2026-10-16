
import ProInventory from "@/features/f11_professional/ProInventory";
import ProShell from "@/features/f11_professional/ProShell";
import { requireSignedInProPreview } from "@/features/f11_professional/pro-server";

export const metadata = {
  title: "HOMIO Pro | Inventory",
  robots: { index: false, follow: false },
};

export const dynamic = "force-dynamic";

export default async function ProInventoryPage() {
  const identity = await requireSignedInProPreview("/pro/inventory");

  return (
    <ProShell identity={identity} activeSection="inventory">
      <ProInventory />
    </ProShell>
  );
}
