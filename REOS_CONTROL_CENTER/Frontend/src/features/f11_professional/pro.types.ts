
export type ProSection =
  | "dashboard"
  | "inventory"
  | "inventory-detail"
  | "leads"
  | "enquiries"
  | "visits"
  | "follow-ups"
  | "clients"
  | "projects"
  | "deals"
  | "documents"
  | "performance";

/**
 * These labels describe permitted role categories only.
 * They do not establish that a signed-in user holds any of these roles.
 */
export type AuthorizedProRole =
  | "HOMIO"
  | "HOMIO_AUTHORIZED_BROKERAGE_OPERATOR"
  | "BUILDER"
  | "OWNER_AUTHORIZED_INVENTORY_PARTNER"
  | "ENTERPRISE_WHITE_LABEL_PARTNER";

export type ProIdentity = Readonly<{
  displayName: string;
  email?: string;
  emailVerified: boolean;
}>;

export type ProNavigationItem = Readonly<{
  section: Exclude<ProSection, "inventory-detail">;
  href: string;
  label: string;
  description: string;
}>;

export type ProSectionMeta = Readonly<{
  title: string;
  description: string;
  eyebrow: string;
}>;

/**
 * Replace these false values only after verified server-side REOS
 * integrations and record-level authorization have been implemented.
 *
 * A signed-in HOMIO session by itself does not authorize professional access.
 */
export const PRO_CAPABILITIES = {
  roleAuthorization: false,
  inventory: false,
  leads: false,
  enquiries: false,
  visits: false,
  followUps: false,
  clients: false,
  projects: false,
  deals: false,
  documents: false,
  performance: false,
} as const;

export const PRO_NAVIGATION: readonly ProNavigationItem[] = [
  {
    section: "dashboard",
    href: "/pro",
    label: "Overview",
    description: "Workspace and connected capabilities",
  },
  {
    section: "inventory",
    href: "/pro/inventory",
    label: "Inventory",
    description: "Authorized inventory records",
  },
  {
    section: "leads",
    href: "/pro/leads",
    label: "Leads",
    description: "Authorized lead records",
  },
  {
    section: "enquiries",
    href: "/pro/enquiries",
    label: "Enquiries",
    description: "Enquiry records and status",
  },
  {
    section: "visits",
    href: "/pro/visits",
    label: "Visits",
    description: "Authorized visit records",
  },
  {
    section: "follow-ups",
    href: "/pro/follow-ups",
    label: "Follow-ups",
    description: "Pending actions from connected services",
  },
  {
    section: "clients",
    href: "/pro/clients",
    label: "Clients",
    description: "Authorized client records",
  },
  {
    section: "projects",
    href: "/pro/projects",
    label: "Projects",
    description: "Authorized project records",
  },
  {
    section: "deals",
    href: "/pro/deals",
    label: "Deals",
    description: "Authorized deal records",
  },
  {
    section: "documents",
    href: "/pro/documents",
    label: "Documents",
    description: "Authorized transaction documents",
  },
  {
    section: "performance",
    href: "/pro/performance",
    label: "Performance",
    description: "Verified service-backed performance",
  },
];

export const PRO_SECTION_META: Record<ProSection, ProSectionMeta> = {
  dashboard: {
    title: "Professional command center",
    description:
      "A unified workspace for authorized HOMIO professional operations.",
    eyebrow: "HOMIO PRO / OVERVIEW",
  },
  inventory: {
    title: "Inventory workspace",
    description:
      "Property records become available after inventory access is verified.",
    eyebrow: "OPERATIONS / INVENTORY",
  },
  "inventory-detail": {
    title: "Inventory record",
    description:
      "A record can be displayed only after server-side authorization succeeds.",
    eyebrow: "OPERATIONS / RECORD DETAIL",
  },
  leads: {
    title: "Lead workspace",
    description:
      "Authorized lead records and their current states, when connected.",
    eyebrow: "RELATIONSHIPS / LEADS",
  },
  enquiries: {
    title: "Enquiry workspace",
    description:
      "Enquiry history and status from an authorized service, when available.",
    eyebrow: "RELATIONSHIPS / ENQUIRIES",
  },
  visits: {
    title: "Visit workspace",
    description:
      "Visit details and scheduling state from the approved service.",
    eyebrow: "OPERATIONS / VISITS",
  },
  "follow-ups": {
    title: "Follow-up workspace",
    description:
      "Follow-up requirements only when their source and authorization are verified.",
    eyebrow: "OPERATIONS / FOLLOW-UPS",
  },
  clients: {
    title: "Client workspace",
    description:
      "Client information must remain scoped to the authorized user and organization.",
    eyebrow: "RELATIONSHIPS / CLIENTS",
  },
  projects: {
    title: "Project workspace",
    description:
      "Authorized project records without invented inventory or availability.",
    eyebrow: "PORTFOLIO / PROJECTS",
  },
  deals: {
    title: "Deal workspace",
    description:
      "Deal states remain controlled by the canonical REOS transaction service.",
    eyebrow: "TRANSACTIONS / DEALS",
  },
  documents: {
    title: "Document workspace",
    description:
      "Only authorized document metadata and access-approved content may be shown.",
    eyebrow: "TRANSACTIONS / DOCUMENTS",
  },
  performance: {
    title: "Performance workspace",
    description:
      "No synthetic KPIs: metrics require verified, attributable source data.",
    eyebrow: "INTELLIGENCE / PERFORMANCE",
  },
};
