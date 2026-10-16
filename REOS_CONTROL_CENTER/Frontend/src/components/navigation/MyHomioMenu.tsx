
/* File: src/components/navigation/MyHomioMenu.tsx */
import MegaMenuPanel from "./MegaMenuPanel";

const items = [
  {
    label: "My HOMIO",
    description: "Open your authenticated account workspace.",
    href: "/my",
  },
  {
    label: "Saved properties",
    description: "Review your saved property experience.",
    href: "/saved",
  },
  {
    label: "Compare",
    description: "Review property and project comparisons.",
    href: "/compare",
  },
  {
    label: "Sign in",
    description: "Continue to your HOMIO account.",
    href: "/login?returnTo=%2Fmy",
  },
] as const;

export default function MyHomioMenu() {
  return (
    <MegaMenuPanel
      eyebrow="YOUR ACCOUNT"
      title="My HOMIO"
      description="Your account and personal discovery tools."
      items={items}
    />
  );
}
