
/* File: src/components/navigation/ServicesMenu.tsx */
import MegaMenuPanel from "./MegaMenuPanel";

const items = [
  {
    label: "Property enquiry",
    description: "Start the configured enquiry flow.",
    href: "/enquiry",
  },
  {
    label: "List a property",
    description: "Property submission preview; creation is not enabled by this link.",
    href: "/#post-property",
    badge: "PREVIEW",
  },
  {
    label: "Search",
    description: "Explore the available property-search experience.",
    href: "/search",
  },
] as const;

export default function ServicesMenu() {
  return (
    <MegaMenuPanel
      eyebrow="SUPPORT"
      title="Services"
      description="Explore supported entry points. Business operations require their approved service integration."
      items={items}
    />
  );
}
