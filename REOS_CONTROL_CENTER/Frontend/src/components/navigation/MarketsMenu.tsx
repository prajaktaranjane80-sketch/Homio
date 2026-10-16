import GlobalMegaMenu from "./GlobalMegaMenu";

const items = [
  { href: "/search?city=Pune", title: "Pune, India", description: "Designated active market policy.", icon: "◎", status: "Active market policy" },
  { href: "/search?city=Dubai", title: "Dubai, UAE", description: "Market experience configured for future activation.", icon: "◈", status: "Built · not operational" },
  { href: "/search?city=Singapore", title: "Singapore", description: "Market experience configured for future activation.", icon: "◇", status: "Built · not operational" },
  { href: "/search?city=Tokyo", title: "Tokyo, Japan", description: "Market experience configured for future activation.", icon: "⌖", status: "Built · not operational" },
  { href: "/search?city=London", title: "London, UK", description: "Market experience configured for future activation.", icon: "↗", status: "Built · not operational" },
  { href: "/search?city=New%20York", title: "New York, USA", description: "Market experience configured for future activation.", icon: "▦", status: "Built · not operational" },
] as const;

export default function MarketsMenu() {
  return (
    <GlobalMegaMenu
      eyebrow="MARKET NETWORK"
      title="Global outlook. Local context."
      description="Pune is designated as the active market. Other markets remain non-operational until approved activation and service checks are complete."
      items={items}
    />
  );
}
