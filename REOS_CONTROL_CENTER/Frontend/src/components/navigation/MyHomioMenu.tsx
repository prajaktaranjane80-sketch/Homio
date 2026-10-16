import GlobalMegaMenu from "./GlobalMegaMenu";

const items = [
  { href: "/my", title: "My HOMIO", description: "Open your signed-in account workspace.", icon: "◇" },
  { href: "/saved", title: "Saved properties", description: "Review saved property discovery items.", icon: "♡" },
  { href: "/compare", title: "Compare", description: "Review supported property comparisons.", icon: "⇄" },
  { href: "/login?returnTo=%2Fmy", title: "Sign in", description: "Continue through the configured authentication flow.", icon: "↗" },
] as const;

export default function MyHomioMenu() {
  return (
    <GlobalMegaMenu
      eyebrow="YOUR SPACE"
      title="A more personal property journey."
      description="Sign-in and account access use HOMIO authentication. Protected information remains subject to server-side authorization."
      items={items}
    />
  );
}
