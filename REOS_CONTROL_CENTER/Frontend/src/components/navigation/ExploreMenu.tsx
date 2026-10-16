
/* File: src/components/navigation/ExploreMenu.tsx */
import MegaMenuPanel from "./MegaMenuPanel";

const items = [
  {
    label: "Property search",
    description: "Explore configured homes and property categories.",
    href: "/search",
  },
  {
    label: "Save & compare",
    description: "Review the properties and projects you have saved.",
    href: "/compare",
  },
  {
    label: "Market overview",
    description: "Read the current market activation and availability context.",
    href: "/#market-intelligence",
  },
] as const;

export default function ExploreMenu() {
  return (
    <MegaMenuPanel
      eyebrow="DISCOVER"
      title="Explore HOMIO"
      description="Move from discovery to informed comparison."
      items={items}
    />
  );
}
