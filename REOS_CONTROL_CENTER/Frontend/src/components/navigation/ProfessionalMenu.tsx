import GlobalMegaMenu from "./GlobalMegaMenu";

const items = [
  { href: "/pro", title: "Professional overview", description: "Open HOMIO Pro's protected workspace preview.", icon: "▦" },
  { href: "/pro/inventory", title: "Inventory", description: "Property records remain unavailable until role access is verified.", icon: "⌂", status: "Authorization required" },
  { href: "/pro/leads", title: "Leads & enquiries", description: "Requires verified professional role and connected services.", icon: "◎", status: "Service not connected" },
  { href: "/pro/deals", title: "Deals & documents", description: "Transaction data remains under REOS authority.", icon: "⇄", status: "Service not connected" },
] as const;

export default function ProfessionalMenu() {
  return (
    <GlobalMegaMenu
      eyebrow="HOMIO PRO"
      title="Professional operations."
      description="For HOMIO and authorized brokerage, builder, owner and enterprise partners—as permitted by the architecture. A menu entry never grants a role."
      items={items}
    />
  );
}
