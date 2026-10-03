import Link from "next/link";

import { ResponsiveNavigation } from "@/components/shell/ResponsiveNavigation";

export function Header() {
  return (
    <header className="site-header">
      <div className="site-header__inner">
        <Link className="brand" href="/" aria-label="HOMIO home">
          <span className="brand__name">HOMIO</span>
          <span className="brand__descriptor">INDIA REAL ESTATE</span>
        </Link>

        <ResponsiveNavigation />
      </div>
    </header>
  );
}