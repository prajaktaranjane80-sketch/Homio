import GlobalMegaMenu from "./GlobalMegaMenu";

const items = [
  { href: "/ai", title: "HOMIO AI", description: "AI experience with clear service boundaries.", icon: "✳" },
  { href: "/#market-intelligence", title: "Market intelligence", description: "Explore market context and preview information.", icon: "◉" },
  { href: "/search", title: "Search insights", description: "Use location and property filters to refine discovery.", icon: "⌕" },
  { href: "/#advice", title: "Advice & guides", description: "Property education and practical guidance.", icon: "▤" },
] as const;

export default function IntelligenceMenu() {
  return (
    <GlobalMegaMenu
      eyebrow="INSIGHTS"
      title="Context before decisions."
      description="Explore property context and learning resources. Unsupported metrics and unverified AI claims are not presented as authoritative data."
      items={items}
    />
  );
}
