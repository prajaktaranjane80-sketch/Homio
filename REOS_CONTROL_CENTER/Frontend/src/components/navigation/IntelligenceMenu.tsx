
/* File: src/components/navigation/IntelligenceMenu.tsx */
import MegaMenuPanel from "./MegaMenuPanel";

const items = [
  {
    label: "HOMIO AI",
    description: "Explore the current AI experience and its limitations.",
    href: "/ai",
  },
  {
    label: "Market context",
    description: "Review market previews without assuming verified statistics.",
    href: "/#market-intelligence",
  },
  {
    label: "Advice",
    description: "Open the existing HOMIO advice section.",
    href: "/#advice",
  },
] as const;

export default function IntelligenceMenu() {
  return (
    <MegaMenuPanel
      eyebrow="INSIGHTS"
      title="Intelligence"
      description="Use context and insights as support for research—not as a substitute for verification."
      items={items}
    />
  );
}
