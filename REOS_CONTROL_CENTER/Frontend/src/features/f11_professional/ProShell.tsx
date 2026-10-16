
import Link from "next/link";
import type { ReactNode } from "react";

import { PRO_NAVIGATION } from "./pro.types";
import type { ProIdentity, ProSection } from "./pro.types";
import styles from "./ProWorkspace.module.css";

const NAV_SYMBOLS: Record<string, string> = {
  dashboard: "⌂",
  inventory: "▤",
  leads: "◎",
  enquiries: "↗",
  visits: "◷",
  "follow-ups": "↻",
  clients: "◇",
  projects: "▦",
  deals: "⇄",
  documents: "▧",
  performance: "⌁",
};

type ProShellProps = Readonly<{
  identity: ProIdentity;
  activeSection: ProSection;
  children: ReactNode;
}>;

function getInitials(name: string): string {
  const initials = name
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part.charAt(0).toUpperCase())
    .join("");

  return initials || "H";
}

export default function ProShell({
  identity,
  activeSection,
  children,
}: ProShellProps) {
  const navigationSection =
    activeSection === "inventory-detail" ? "inventory" : activeSection;

  const initials = getInitials(identity.displayName);

  return (
    <div className={styles.app}>
      <a className={styles.skipLink} href="#pro-main">
        Skip to workspace content
      </a>

      <div className={styles.frame}>
        <aside className={styles.sidebar} aria-label="HOMIO Pro navigation">
          <Link href="/pro" className={styles.brand} aria-label="HOMIO Pro overview">
            <span className={styles.brandMark} aria-hidden="true">
              H
            </span>

            <span className={styles.brandCopy}>
              <span className={styles.brandName}>HOMIO</span>
              <span className={styles.brandSubtitle}>Professional OS</span>
            </span>
          </Link>

          <p className={styles.sideCaption}>Workspace navigation</p>

          <nav className={styles.navigation} aria-label="Professional sections">
            {PRO_NAVIGATION.map((item) => {
              const isActive = navigationSection === item.section;

              return (
                <Link
                  key={item.section}
                  href={item.href}
                  className={
                    isActive
                      ? `${styles.navLink} ${styles.navLinkActive}`
                      : styles.navLink
                  }
                  aria-current={isActive ? "page" : undefined}
                  title={item.description}
                >
                  <span className={styles.navSymbol} aria-hidden="true">
                    {NAV_SYMBOLS[item.section] ?? "·"}
                  </span>

                  <span className={styles.navText}>{item.label}</span>

                  {isActive ? (
                    <span className={styles.navMeta} aria-hidden="true">
                      ACTIVE
                    </span>
                  ) : null}
                </Link>
              );
            })}
          </nav>

          <div className={styles.sidebarSpacer} />

          <section className={styles.sideStatus} aria-labelledby="pro-side-status">
            <div className={styles.sideStatusHead}>
              <span className={styles.sideStatusDot} aria-hidden="true" />
              <span id="pro-side-status">Access boundary active</span>
            </div>

            <p className={styles.sideStatusText}>
              Professional role authorization is not connected. Restricted
              business data remains unavailable until verified by the server.
            </p>
          </section>

          <p className={styles.sideFootnote}>
            HOMIO Pro preview
            <br />
            REOS remains the business authority.
          </p>
        </aside>

        <div className={styles.mainColumn}>
          <header className={styles.topbar}>
            <div className={styles.crumbGroup}>
              <div className={styles.crumb}>
                HOMIO <span aria-hidden="true">/</span>{" "}
                <span className={styles.crumbStrong}>Professional operations</span>
              </div>
              <div className={styles.topbarLabel}>
                Authorized workspace preview
              </div>
            </div>

            <div className={styles.topbarRight}>
              <span className={styles.previewPill}>
                <span className={styles.previewDot} aria-hidden="true" />
                PREVIEW MODE
              </span>

              <Link href="/my" className={styles.accountLink}>
                My HOMIO
              </Link>

              <div className={styles.identity}>
                <span className={styles.avatar} aria-hidden="true">
                  {initials}
                </span>

                <span className={styles.identityText}>
                  <span className={styles.identityName}>
                    {identity.displayName}
                  </span>
                  <span className={styles.identityEmail}>
                    {identity.email || "Account email unavailable"}
                  </span>
                </span>
              </div>
            </div>
          </header>

          <main id="pro-main" className={styles.content} tabIndex={-1}>
            <aside
              className={styles.accessBanner}
              aria-labelledby="pro-access-title"
            >
              <span className={styles.accessIcon} aria-hidden="true">
                !
              </span>

              <div className={styles.accessCopy}>
                <h2 id="pro-access-title" className={styles.accessTitle}>
                  Professional role not verified
                </h2>

                <p className={styles.accessText}>
                  {identity.emailVerified
                    ? "Your account email is verified, but this does not grant a professional role. Protected workspaces and records remain unavailable until the relevant server-side REOS authorization capability is connected."
                    : "Your HOMIO session is available, but your professional role and organization access have not been verified. Protected workspaces and records remain unavailable."}
                </p>
              </div>
            </aside>

            {children}
          </main>
        </div>
      </div>
    </div>
  );
}
