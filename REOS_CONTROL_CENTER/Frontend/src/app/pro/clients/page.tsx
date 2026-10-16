
import ProClients from "@/features/f11_professional/ProClients";
import ProShell from "@/features/f11_professional/ProShell";
import { requireSignedInProPreview } from "@/features/f11_professional/pro-server";

export const metadata = {
  title: "HOMIO Pro | Clients",
  robots: { index: false, follow: false },
};

export const dynamic = "force-dynamic";

export default async function ProClientsPage() {
  const identity = await requireSignedInProPreview("/pro/clients");

  return (
    <ProShell identity={identity} activeSection="clients">
      <ProClients />
    </ProShell>
  );
}
