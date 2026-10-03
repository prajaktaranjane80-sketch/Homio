import { HomeHeader } from "@/components/home/HomeHeader";
import { HomeHero } from "@/components/home/HomeHero";
import { HomeQuickDiscovery } from "@/components/home/HomeQuickDiscovery";
import { HomeSecondaryNav } from "@/components/home/HomeSecondaryNav";
import { AppShell } from "@/components/shell/AppShell";

export default function HomePage() {
  return (
    <AppShell header={<HomeHeader />}>
      <main id="main-content" className="page-shell">
        <HomeSecondaryNav />
        <HomeHero />
        <HomeQuickDiscovery />

        <section className="home-build-next" aria-labelledby="next-sections-title">
          <div className="page-container">
            <span className="home-eyebrow">HOMIO DISCOVERY</span>

            <h2 id="next-sections-title">
              Projects, properties, localities and the HOMIO brokerage journey.
            </h2>

            <p>
              These discovery sections are added in sequence from the HOMIO
              Website Master File.
            </p>
          </div>
        </section>
      </main>
    </AppShell>
  );
}
