
/* File: src/components/navigation/ProfessionalMenu.tsx */
import MegaMenuPanel from "./MegaMenuPanel";

const items = [
  {
    label: "Professional workspace",
    description: "Open the session-gated HOMIO Pro preview.",
    href: "/pro",
    badge: "ROLE CHECK REQUIRED",
  },
  {
    label: "List a property",
    description: "Submission is not activated through this navigation preview.",
    href: "/#post-property",
    badge: "PREVIEW",
  },
] as const;

export default function ProfessionalMenu() {
  return (
    <MegaMenuPanel
      eyebrow="AUTHORIZED OPERATIONS"
      title="HOMIO Pro"
      description="Professional capabilities require a verified role and approved REOS services."
      items={items}
    />
  );
}
