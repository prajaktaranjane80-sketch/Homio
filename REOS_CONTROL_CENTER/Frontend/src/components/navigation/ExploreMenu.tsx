import GlobalMegaMenu from "./GlobalMegaMenu";

const items = [
  { href: "/search?intent=buy", title: "Buy a property", description: "Explore homes and properties for purchase.", icon: "⌂" },
  { href: "/search?intent=rent", title: "Rent a property", description: "Explore properties for rent.", icon: "⌑" },
  { href: "/search?intent=commercial", title: "Commercial spaces", description: "Search office and business property categories.", icon: "▦" },
  { href: "/search", title: "Search HOMIO", description: "Open property search and available filters.", icon: "⌕" },
] as const;

export default function ExploreMenu() {
  return (
    <GlobalMegaMenu
      eyebrow="DISCOVER"
      title="Explore property your way."
      description="Move from broad discovery to a more focused property search. Results depend on configured data sources."
      items={items}
    />
  );
}
