
import ProEnquiries from "@/features/f11_professional/ProEnquiries";
import ProShell from "@/features/f11_professional/ProShell";
import { requireSignedInProPreview } from "@/features/f11_professional/pro-server";

export const metadata = {
  title: "HOMIO Pro | Enquiries",
  robots: { index: false, follow: false },
};

export const dynamic = "force-dynamic";

export default async function ProEnquiriesPage() {
  const identity = await requireSignedInProPreview("/pro/enquiries");

  return (
    <ProShell identity={identity} activeSection="enquiries">
      <ProEnquiries />
    </ProShell>
  );
}
