
/* File: src/components/navigation/GlobalMegaMenu.tsx */
import ExploreMenu from "./ExploreMenu";
import IntelligenceMenu from "./IntelligenceMenu";
import MarketsMenu from "./MarketsMenu";
import MegaMenuStyles from "./MegaMenu.module.css";
import MyHomioMenu from "./MyHomioMenu";
import ProfessionalMenu from "./ProfessionalMenu";
import ServicesMenu from "./ServicesMenu";

export default function GlobalMegaMenu() {
  return (
    <nav className={MegaMenuStyles.megaNav} aria-label="HOMIO global navigation">
      <div className={MegaMenuStyles.megaGrid}>
        <ExploreMenu />
        <MarketsMenu />
        <IntelligenceMenu />
        <ServicesMenu />
        <MyHomioMenu />
        <ProfessionalMenu />
      </div>
    </nav>
  );
}
