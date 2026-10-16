
/* File: src/components/navigation/MobileMegaMenu.tsx */
"use client";

import ExploreMenu from "./ExploreMenu";
import IntelligenceMenu from "./IntelligenceMenu";
import MarketsMenu from "./MarketsMenu";
import MegaMenuStyles from "./MegaMenu.module.css";
import MyHomioMenu from "./MyHomioMenu";
import ProfessionalMenu from "./ProfessionalMenu";
import ServicesMenu from "./ServicesMenu";

type Props = Readonly<{
  isOpen: boolean;
  onClose: () => void;
}>;

export default function MobileMegaMenu({ isOpen, onClose }: Props) {
  if (!isOpen) return null;

  return (
    <aside
      className={MegaMenuStyles.mobilePanel}
      aria-label="Mobile navigation"
    >
      <header className={MegaMenuStyles.mobileHeader}>
        <div className={MegaMenuStyles.mobileBrand}>
          HOMIO
          <span>GLOBAL REAL ESTATE</span>
        </div>

        <button
          type="button"
          className={MegaMenuStyles.closeButton}
          onClick={onClose}
          aria-label="Close navigation"
        >
          ×
        </button>
      </header>

      <div className={MegaMenuStyles.mobileSections}>
        <ExploreMenu />
        <MarketsMenu />
        <IntelligenceMenu />
        <ServicesMenu />
        <MyHomioMenu />
        <ProfessionalMenu />
      </div>
    </aside>
  );
}
