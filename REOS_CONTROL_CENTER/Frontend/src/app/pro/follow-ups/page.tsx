
import ProFollowUps from "@/features/f11_professional/ProFollowUps";
import ProShell from "@/features/f11_professional/ProShell";
import { requireSignedInProPreview } from "@/features/f11_professional/pro-server";

export const metadata = {
  title: "HOMIO Pro | Follow-ups",
  robots: { index: false, follow: false },
};

export const dynamic = "force-dynamic";

export default async function ProFollowUpsPage() {
  const identity = await requireSignedInProPreview("/pro/follow-ups");

  return (
    <ProShell identity={identity} activeSection="follow-ups">
      <ProFollowUps />
    </ProShell>
  );
}
