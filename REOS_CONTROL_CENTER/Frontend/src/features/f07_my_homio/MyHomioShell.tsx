"use client";

import { useState } from "react";

import { useSaveCompareSession } from "@/features/f06_save_compare/saveCompareSession";

import { useMyHomioActivity } from "./myHomioActivityStore";

import type {
  MyHomioNavigationGroup,
  MyHomioNavigationItem,
  MyHomioProfile,
  MyHomioSection,
} from "./my-homio.types";

import MyHomioDashboard from "./MyHomioDashboard";
import MyHomioProfilePage from "./MyHomioProfile";
import MyHomioSaved from "./MyHomioSaved";
import MyHomioCompare from "./MyHomioCompare";
import MyHomioRecentSearches from "./MyHomioRecentSearches";
import MyHomioRecentViews from "./MyHomioRecentViews";
import MyHomioEnquiries from "./MyHomioEnquiries";
import MyHomioConversations from "./MyHomioConversations";
import MyHomioVisits from "./MyHomioVisits";
import MyHomioRecommendations from "./MyHomioRecommendations";
import MyHomioBrokerageJourney from "./MyHomioBrokerageJourney";
import MyHomioDocuments from "./MyHomioDocuments";
import MyHomioNotifications from "./MyHomioNotifications";
import MyHomioSettings from "./MyHomioSettings";

import styles from "./MyHomio.module.css";

type Props = Readonly<{
  profile: MyHomioProfile;
}>;

const NAV_ITEMS: readonly MyHomioNavigationItem[] = [
  {
    id: "dashboard",
    label: "Overview",
    group: "overview",
    description: "Your current activity and return paths.",
  },
  {
    id: "saved",
    label: "Saved items",
    group: "discovery",
    description: "Properties and projects saved in this session.",
  },
  {
    id: "compare",
    label: "Compare options",
    group: "discovery",
    description: "Your current F06 comparison.",
  },
  {
    id: "recent-searches",
    label: "Search activity",
    group: "discovery",
    description: "Recent searches and saved requirements.",
  },
  {
    id: "recent-views",
    label: "Viewed properties",
    group: "discovery",
    description: "Property and project views in this browser tab.",
  },
  {
    id: "enquiries",
    label: "Enquiries",
    group: "journey",
    description: "Enquiry records from the authorized service.",
  },
  {
    id: "conversations",
    label: "Conversations",
    group: "journey",
    description: "Messages from connected account conversations.",
  },
  {
    id: "visits",
    label: "Visits",
    group: "journey",
    description: "Visit requests and confirmations from the visit service.",
  },
  {
    id: "brokerage-journey",
    label: "Property journey",
    group: "journey",
    description: "Reported brokerage milestones, not inferred progress.",
  },
  {
    id: "recommendations",
    label: "Recommendations",
    group: "journey",
    description: "Relevant recommendations from an approved source.",
  },
  {
    id: "profile",
    label: "My profile",
    group: "account",
    description: "Identity-provider profile claims.",
  },
  {
    id: "documents",
    label: "Documents",
    group: "account",
    description: "Documents from authorized account storage.",
  },
  {
    id: "notifications",
    label: "Notifications",
    group: "account",
    description: "Account updates from the notification service.",
  },
  {
    id: "settings",
    label: "Settings & privacy",
    group: "account",
    description: "Session controls and current integration state.",
  },
];

const NAV_GROUPS: readonly {
  id: MyHomioNavigationGroup;
  label: string;
}[] = [
  { id: "overview", label: "My space" },
  { id: "discovery", label: "My activity" },
  { id: "journey", label: "Property journey" },
  { id: "account", label: "Account" },
];

const NAV_GLYPHS: Partial<Record<MyHomioSection, string>> = {
  dashboard: "OV",
  saved: "SV",
  compare: "⇄",
  "recent-searches": "⌕",
  "recent-views": "↗",
  enquiries: "EN",
  conversations: "MS",
  visits: "VS",
  "brokerage-journey": "JR",
  recommendations: "RC",
  profile: "ID",
  documents: "DC",
  notifications: "NT",
  settings: "ST",
};

export default function MyHomioShell({ profile }: Props) {
  const [activeSection, setActiveSection] =
    useState<MyHomioSection>("dashboard");

  const saveCompare = useSaveCompareSession();
  const activity = useMyHomioActivity();

  const displayName = profile.name?.trim() || "HOMIO member";
  const activeItem = NAV_ITEMS.find(
    (item) => item.id === activeSection,
  );

  function countFor(section: MyHomioSection): number | undefined {
    switch (section) {
      case "saved":
        return saveCompare.savedRecords.length;
      case "compare":
        return saveCompare.comparedItems.length;
      case "recent-searches":
        return (
          activity.recentSearches.length +
          activity.savedSearches.length
        );
      case "recent-views":
        return activity.recentViews.length;
      default:
        return undefined;
    }
  }

  function renderSection() {
    switch (activeSection) {
      case "dashboard":
        return (
          <MyHomioDashboard
            profile={profile}
            onNavigate={setActiveSection}
          />
        );
      case "profile":
        return <MyHomioProfilePage profile={profile} />;
      case "saved":
        return <MyHomioSaved />;
      case "compare":
        return <MyHomioCompare />;
      case "recent-searches":
        return <MyHomioRecentSearches />;
      case "recent-views":
        return <MyHomioRecentViews />;
      case "enquiries":
        return <MyHomioEnquiries />;
      case "conversations":
        return <MyHomioConversations />;
      case "visits":
        return <MyHomioVisits />;
      case "recommendations":
        return <MyHomioRecommendations />;
      case "brokerage-journey":
        return <MyHomioBrokerageJourney />;
      case "documents":
        return <MyHomioDocuments />;
      case "notifications":
        return <MyHomioNotifications />;
      case "settings":
        return <MyHomioSettings profile={profile} />;
    }
  }

  return (
    <main className={styles.shell}>
      <div className={styles.inner}>
        <header className={styles.hero}>
          <div className={styles.heroMain}>
            <p className={styles.eyebrow}>
              MY HOMIO / YOUR PRIVATE WORKSPACE
            </p>

            <h1 className={styles.heroTitle}>
              Your property decisions.
              <br />
              <em>One considered space.</em>
            </h1>

            <p className={styles.heroText}>
              Pick up where your search left off. Keep shortlisted
              options close, compare the details that matter, and
              follow your property journey as connected services report it.
            </p>

            <div className={styles.heroActions}>
              <a
                className={`${styles.button} ${styles.buttonPrimary}`}
                href="/search"
              >
                Continue discovery <span aria-hidden="true">↗</span>
              </a>

              <span className={styles.heroHint}>
                Private account workspace · Authenticated session
              </span>
            </div>
          </div>

          <aside className={styles.heroAside} aria-label="Account identity">
            <span className={styles.memberLabel}>SIGNED-IN PROFILE</span>
            <strong className={styles.memberName}>{displayName}</strong>
            <span className={styles.memberEmail}>
              {profile.email || "Email not supplied by identity provider"}
            </span>

            <div className={styles.memberMeta}>
              <span>Email verification</span>
              <strong>
                {profile.emailVerified ? "Verified" : "Not confirmed"}
              </strong>
            </div>

            <div className={styles.memberMeta}>
              <span>Search persistence</span>
              <strong>Browser session</strong>
            </div>

            <form action="/api/auth/logout" method="post">
              <button
                type="submit"
                className={`${styles.button} ${styles.buttonQuiet}`}
                style={{ width: "100%", marginTop: 16 }}
              >
                Sign out securely
              </button>
            </form>
          </aside>
        </header>

        <div className={styles.statsGrid} aria-label="Current activity">
          <article className={styles.statCard}>
            <div className={styles.statTop}>
              <span className={styles.statLabel}>Saved shortlist</span>
              <span className={styles.statGlyph} aria-hidden="true">♡</span>
            </div>
            <strong className={styles.statValue}>
              {saveCompare.savedRecords.length.toString().padStart(2, "0")}
            </strong>
            <span className={styles.statFoot}>
              Current F06 browser-session items
            </span>
          </article>

          <article className={styles.statCard}>
            <div className={styles.statTop}>
              <span className={styles.statLabel}>Compare board</span>
              <span className={styles.statGlyph} aria-hidden="true">⇄</span>
            </div>
            <strong className={styles.statValue}>
              {saveCompare.comparedItems.length}/4
            </strong>
            <span className={styles.statFoot}>
              Comparison slots currently in use
            </span>
          </article>

          <article className={styles.statCard}>
            <div className={styles.statTop}>
              <span className={styles.statLabel}>Search activity</span>
              <span className={styles.statGlyph} aria-hidden="true">⌕</span>
            </div>
            <strong className={styles.statValue}>
              {activity.recentSearches.length.toString().padStart(2, "0")}
            </strong>
            <span className={styles.statFoot}>
              Recent searches in this browser tab
            </span>
          </article>

          <article className={styles.statCard}>
            <div className={styles.statTop}>
              <span className={styles.statLabel}>Viewed previews</span>
              <span className={styles.statGlyph} aria-hidden="true">↗</span>
            </div>
            <strong className={styles.statValue}>
              {activity.recentViews.length.toString().padStart(2, "0")}
            </strong>
            <span className={styles.statFoot}>
              Property and project pages visited in this tab
            </span>
          </article>
        </div>

        <div className={styles.layout}>
          <nav className={styles.navigation} aria-label="My HOMIO navigation">
            {NAV_GROUPS.map((group) => {
              const items = NAV_ITEMS.filter(
                (item) => item.group === group.id,
              );

              return (
                <section className={styles.navGroup} key={group.id}>
                  <h2 className={styles.navGroupLabel}>{group.label}</h2>

                  <div className={styles.navList}>
                    {items.map((item) => {
                      const selected = item.id === activeSection;
                      const count = countFor(item.id);

                      return (
                        <button
                          key={item.id}
                          type="button"
                          className={[
                            styles.navButton,
                            selected ? styles.navButtonActive : "",
                          ].join(" ")}
                          aria-current={selected ? "page" : undefined}
                          aria-label={item.description}
                          title={item.description}
                          onClick={() => setActiveSection(item.id)}
                        >
                          <span className={styles.navIcon} aria-hidden="true">
                            {NAV_GLYPHS[item.id] ?? "•"}
                          </span>

                          <span className={styles.navLabel}>
                            {item.label}
                          </span>

                          {count !== undefined ? (
                            <span className={styles.navCount}>
                              {count}
                            </span>
                          ) : null}
                        </button>
                      );
                    })}
                  </div>
                </section>
              );
            })}
          </nav>

          <section className={styles.workspacePanel} aria-labelledby="active-workspace-heading">
            <div className={styles.panelHeader}>
              <p className={styles.kicker}>MY HOMIO / {activeItem?.group}</p>
              <h2
                id="active-workspace-heading"
                className={styles.panelTitle}
              >
                {activeItem?.label ?? "Overview"}
              </h2>
              <p className={styles.panelLead}>
                {activeItem?.description ?? "Your private HOMIO workspace."}
              </p>
            </div>

            {renderSection()}
          </section>
        </div>

        <footer className={styles.footer}>
          Private account workspace · Saved and Compare use F06's current
          browser-memory store. Search activity is retained for this browser
          tab only. Account synchronization and service-owned events are not
          claimed unless their authorized source is connected.
        </footer>
      </div>
    </main>
  );
}
