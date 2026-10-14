import type { Metadata } from "next";

import AIWorkspace from "@/features/f08_ai/AIWorkspace";

export const metadata: Metadata = {
  title: "HOMIO AI | Property Decision Workspace",
  description:
    "Shape your real-estate brief, prepare comparisons and continue into HOMIO property discovery.",
};

export default function AIPage() {
  return <AIWorkspace />;
}
