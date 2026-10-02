import Link from "next/link";

import { GlobalSearch } from "@/components/navigation/GlobalSearch";
import { ResponsiveNavigation } from "@/components/shell/ResponsiveNavigation";

export function Header() {
  return (
    <header className="site-header">
      <div className="site-header__inner">
        <Link className="brand" href="/" aria-label="HOMIO home">
          <span className="brand__name">HOMIO</span>
          <span className="brand__descriptor">REAL ESTATE OS</span>
        </Link>

        <div className="site-header__search">
          <GlobalSearch />
        </div>

        <ResponsiveNavigation />
      </div>
    </header>
  );
}
