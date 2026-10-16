
import { notFound } from "next/navigation";

import ProInventoryDetail from "@/features/f11_professional/ProInventoryDetail";
import ProShell from "@/features/f11_professional/ProShell";
import { requireSignedInProPreview } from "@/features/f11_professional/pro-server";

export const metadata = {
  title: "HOMIO Pro | Inventory Record",
  robots: { index: false, follow: false },
};

export const dynamic = "force-dynamic";

type ProInventoryDetailPageProps = Readonly<{
  params: Promise<{ inventoryId: string }>;
}>;

const INVENTORY_ID_PATTERN =
  /^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$/;

export default async function ProInventoryDetailPage({
  params,
}: ProInventoryDetailPageProps) {
  const { inventoryId } = await params;

  const identity = await requireSignedInProPreview(
    `/pro/inventory/${inventoryId}`,
  );

  if (!INVENTORY_ID_PATTERN.test(inventoryId)) {
    notFound();
  }

  return (
    <ProShell identity={identity} activeSection="inventory-detail">
      <ProInventoryDetail recordId={inventoryId} />
    </ProShell>
  );
}
