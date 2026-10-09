import type { ProjectRecord } from "./project.types";

export const PROJECT_PREVIEW: ProjectRecord = {
  id: "homio-kalyani-residences-001",
  name: "HOMIO Kalyani Residences",
  shortName: "Kalyani Residences",
  kind: "project",
  kindLabel: "Project experience",
  location: "Kalyani Nagar, Pune",
  locality: "Kalyani Nagar",
  city: "Pune",
  country: "India",
  developerName: "Experience preview",
  status: "Preview / Experience-ready",
  priceFrom: "₹1.42 Cr",
  priceContext: "Experience preview starting value",
  configurations: ["2 BHK", "3 BHK", "4 BHK", "Penthouse"],
  areaRange: "1,220–2,950 sq.ft.",
  possession: "Preview information",
  collectionName: "Pune Connected Living Collection",
  description:
    "A HOMIO project-experience preview. Project details, price, inventory and verification are not authoritative REOS data.",
  verified: false,
  verificationLabel: "Project verification pending",
  media: [
    { id: "project-media-01", label: "Project exterior", type: "image" },
    { id: "project-media-02", label: "Project lifestyle", type: "image" },
    { id: "project-media-03", label: "Project master plan", type: "master-plan" },
    { id: "project-media-04", label: "Project walkthrough", type: "video" },
    { id: "project-media-05", label: "Virtual project view", type: "virtual" },
  ],
  facts: [
    { label: "Configuration", value: "Preview information" },
    { label: "Area range", value: "Preview information" },
    { label: "Location", value: "Kalyani Nagar, Pune" },
    { label: "Possession", value: "Preview information" },
    { label: "Project type", value: "Residential preview" },
    { label: "Inventory", value: "Preview opportunities" },
  ],
  amenities: [
    { label: "Clubhouse", value: "Preview information" },
    { label: "Swimming pool", value: "Preview information" },
    { label: "Fitness centre", value: "Preview information" },
    { label: "Landscaped spaces", value: "Preview information" },
    { label: "Parking", value: "Preview information" },
    { label: "Security", value: "Preview information" },
    { label: "Power backup", value: "Preview information" },
    { label: "Community lounge", value: "Preview information" },
  ],
  nearby: [
    { label: "Airport", value: "Preview information" },
    { label: "Business districts", value: "Preview information" },
    { label: "Schools", value: "Preview information" },
    { label: "Retail & dining", value: "Preview information" },
  ],
  opportunities: [
    {
      id: "opportunity-3bhk-001",
      title: "Contemporary 3 BHK Residence",
      configuration: "3 BHK",
      price: "₹2.35 Cr",
      area: "1,850 sq.ft.",
      status: "Preview opportunity",
      context: "Experience preview — not verified",
      href: "/property/pune-kalyani-nagar-001",
    },
    {
      id: "opportunity-2bhk-002",
      title: "Modern 2 BHK Residence",
      configuration: "2 BHK",
      price: "Preview only",
      area: "Preview information",
      status: "Preview opportunity",
      context: "Not verified",
    },
    {
      id: "opportunity-4bhk-003",
      title: "Large 4 BHK Residence",
      configuration: "4 BHK",
      price: "Preview only",
      area: "Preview information",
      status: "Preview opportunity",
      context: "Not verified",
    },
  ],
  inventorySummary: {
    totalLabel: "Preview opportunities",
    residentialLabel: "Residential discovery",
    commercialLabel: "Commercial not represented in this preview",
    availabilityLabel: "Preview availability",
  },
  relatedProjects: [
    {
      id: "pune-east-collection-001",
      name: "Pune East Residences",
      location: "Viman Nagar, Pune",
      highlight: "Connected city living",
    },
    {
      id: "baner-urban-collection-001",
      name: "Baner Urban Collection",
      location: "Baner, Pune",
      highlight: "Contemporary city homes",
    },
    {
      id: "aundh-premium-collection-001",
      name: "Aundh Premium Collection",
      location: "Aundh, Pune",
      highlight: "Established neighbourhood living",
    },
  ],
};

type ProjectPreviewInput = Readonly<{
  id: string;
  name: string;
  shortName: string;
  kind: "project" | "collection";
  location: string;
  locality: string;
  city: string;
  country: string;
  collectionName?: string;
}>;

function createProjectPreview(
  input: ProjectPreviewInput,
): ProjectRecord {
  const collectionFields =
    input.kind === "collection"
      ? { collectionName: input.collectionName ?? input.name }
      : {};

  return {
    id: input.id,
    name: input.name,
    shortName: input.shortName,
    kind: input.kind,
    kindLabel:
      input.kind === "collection"
        ? "Collection preview"
        : "Project preview",
    location: input.location,
    locality: input.locality,
    city: input.city,
    country: input.country,
    developerName: "Experience preview",
    status: "Experience preview — not verified",
    priceFrom: "Preview only",
    priceContext: "No verified pricing in this preview",
    configurations: ["Preview information"],
    areaRange: "Preview information",
    possession: "Preview information",
    ...collectionFields,
    description:
      "This HOMIO route preview exists to validate project navigation and page composition. Project facts, pricing, inventory, media and verification require authoritative data.",
    verified: false,
    verificationLabel: "Verification pending",
    media: [
      { id: `${input.id}-media-01`, label: "Image placeholder", type: "image" },
      { id: `${input.id}-media-02`, label: "Lifestyle placeholder", type: "image" },
      { id: `${input.id}-media-03`, label: "Plan placeholder", type: "master-plan" },
    ],
    facts: [
      { label: "Location", value: input.location },
      { label: "Configuration", value: "Preview information" },
      { label: "Pricing", value: "Not verified" },
      { label: "Inventory", value: "Not connected" },
    ],
    amenities: [
      { label: "Amenities", value: "Preview information" },
    ],
    nearby: [
      { label: "Location details", value: "Preview information" },
    ],
    opportunities: [],
    inventorySummary: {
      totalLabel: "Preview inventory not connected",
      residentialLabel: "Preview only",
      commercialLabel: "No verified data",
      availabilityLabel: "Not available in this preview",
    },
    relatedProjects: [],
  };
}

const PROJECT_PREVIEW_VARIANTS: Record<string, ProjectRecord> = {
  "pune-east-collection-001": createProjectPreview({
    id: "pune-east-collection-001",
    name: "Pune East Residences",
    shortName: "Pune East",
    kind: "collection",
    location: "Viman Nagar, Pune",
    locality: "Viman Nagar",
    city: "Pune",
    country: "India",
  }),
  "baner-urban-collection-001": createProjectPreview({
    id: "baner-urban-collection-001",
    name: "Baner Urban Collection",
    shortName: "Baner Urban",
    kind: "collection",
    location: "Baner, Pune",
    locality: "Baner",
    city: "Pune",
    country: "India",
  }),
  "aundh-premium-collection-001": createProjectPreview({
    id: "aundh-premium-collection-001",
    name: "Aundh Premium Collection",
    shortName: "Aundh Premium",
    kind: "collection",
    location: "Aundh, Pune",
    locality: "Aundh",
    city: "Pune",
    country: "India",
  }),
  "harbour-residences": createProjectPreview({
    id: "harbour-residences",
    name: "Harbour Residences",
    shortName: "Harbour Residences",
    kind: "project",
    location: "Dubai Harbour",
    locality: "Dubai Harbour",
    city: "Dubai",
    country: "United Arab Emirates",
  }),
  "marina-crest": createProjectPreview({
    id: "marina-crest",
    name: "Marina Crest",
    shortName: "Marina Crest",
    kind: "project",
    location: "Dubai Marina",
    locality: "Dubai Marina",
    city: "Dubai",
    country: "United Arab Emirates",
  }),
  "the-meridian": createProjectPreview({
    id: "the-meridian",
    name: "The Meridian",
    shortName: "The Meridian",
    kind: "project",
    location: "Singapore",
    locality: "Singapore",
    city: "Singapore",
    country: "Singapore",
  }),
};

export function getProjectPreview(
  projectId: string,
): ProjectRecord | null {
  if (projectId === PROJECT_PREVIEW.id) {
    return { ...PROJECT_PREVIEW };
  }

  const variant = PROJECT_PREVIEW_VARIANTS[projectId];

  return variant ? { ...variant } : null;
}
