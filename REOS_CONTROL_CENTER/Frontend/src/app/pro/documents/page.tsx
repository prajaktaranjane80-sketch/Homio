
import ProDocuments from "@/features/f11_professional/ProDocuments";
import ProShell from "@/features/f11_professional/ProShell";
import { requireSignedInProPreview } from "@/features/f11_professional/pro-server";

export const metadata = {
  title: "HOMIO Pro | Documents",
  robots: { index: false, follow: false },
};

export const dynamic = "force-dynamic";

export default async function ProDocumentsPage() {
  const identity = await requireSignedInProPreview("/pro/documents");

  return (
    <ProShell identity={identity} activeSection="documents">
      <ProDocuments />
    </ProShell>
  );
}
