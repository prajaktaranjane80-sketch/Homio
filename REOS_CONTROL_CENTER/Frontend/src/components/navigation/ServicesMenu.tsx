import GlobalMegaMenu from "./GlobalMegaMenu";

const items = [
  { href: "/enquiry", title: "Property enquiry", description: "Start an enquiry where the service is available.", icon: "↗" },
  { href: "/search", title: "Property discovery", description: "Find configured property and project results.", icon: "⌕" },
  { href: "/pro", title: "Professional workspace", description: "Access the protected HOMIO Pro preview.", icon: "▦" },
  { href: "/#post-property", title: "List with HOMIO", description: "Review the property-submission experience preview.", icon: "＋" },
] as const;

export default function ServicesMenu() {
  return (
    <GlobalMegaMenu
      eyebrow="HOMIO SERVICES"
      title="Every next step, clearly defined."
      description="Service actions are enabled only when their required operational integrations are connected and authorized."
      items={items}
    />
  );
}
