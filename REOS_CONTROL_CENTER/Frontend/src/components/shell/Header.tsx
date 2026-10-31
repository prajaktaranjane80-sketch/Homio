import Image from "next/image";
import Link from "next/link";

import { GlobalSearch } from "@/components/navigation/GlobalSearch";
import { ResponsiveNavigation } from "@/components/shell/ResponsiveNavigation";

export function Header() {
  return (
    <header className="site-header">
      <div className="site-header__inner">
        <Link
          className="brand"
          href="/"
          aria-label="HOMIO home"
        >
          <Image
            className="brand__logo"
            src="/brand/homio-advisor-letter.svg"
            alt=""
            width={222}
            height={47}
            priority
            style={{
              display: "block",
              width: "clamp(9rem, 20vw, 13.875rem)",
              maxWidth: "100%",
              height: "auto",
            }}
          />
        </Link>

        <div className="site-header__search">
          <GlobalSearch />
        </div>

        <ResponsiveNavigation />
      </div>
    </header>
  );
}
