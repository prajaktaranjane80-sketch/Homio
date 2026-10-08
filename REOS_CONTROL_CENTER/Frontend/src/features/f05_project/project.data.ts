import type { ProjectRecord } from "./project.types";

/**
 * F05 experience preview only.
 *
 * This object is not canonical project or inventory data.
 * Verified REOS project/inventory capabilities must replace this adapter
 * when the integration contract is available.
 */
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
  configurations: [
    "2 BHK",
    "3 BHK",
    "4 BHK",
    "Penthouse",
  ],
  areaRange: "1,220–2,950 sq.ft.",
  possession: "Preview information",
  collectionName: "Pune Connected Living Collection",
  description:
    "A HOMIO project-experience preview designed to show how project context, available opportunities, location, amenities and individual property discovery work as one connected journey.",
  verified: false,
  verificationLabel: "Project verification pending",
  media: [
    {
      id: "project-media-01",
      label: "Project exterior",
      type: "image",
    },
    {
      id: "project-media-02",
      label: "Project lifestyle",
      type: "image",
    },
    {
      id: "project-media-03",
      label: "Project master plan",
      type: "master-plan",
    },
    {
      id: "project-media-04",
      label: "Project walkthrough",
      type: "video",
    },
    {
      id: "project-media-05",
      label: "Virtual project view",
      type: "virtual",
    },
  ],
  facts: [
    {
      label: "Configuration",
      value: "2, 3, 4 BHK + Penthouse",
    },
    {
      label: "Area range",
      value: "1,220–2,950 sq.ft.",
    },
    {
      label: "Location",
      value: "Kalyani Nagar, Pune",
    },
    {
      label: "Possession",
      value: "Preview information",
    },
    {
      label: "Project type",
      value: "Residential",
    },
    {
      label: "Inventory",
      value: "Preview opportunities",
    },
  ],
  amenities: [
    { label: "Clubhouse", value: "Preview information" },
    { label: "Swimming pool", value: "Preview information" },
    { label: "Fitness centre", value: "Preview information" },
    {
      label: "Landscaped spaces",
      value: "Preview information",
    },
    { label: "Parking", value: "Preview information" },
    { label: "Security", value: "Preview information" },
    { label: "Power backup", value: "Preview information" },
    {
      label: "Community lounge",
      value: "Preview information",
    },
  ],
  nearby: [
    { label: "Airport", value: "Preview information" },
    {
      label: "Business districts",
      value: "Preview information",
    },
    { label: "Schools", value: "Preview information" },
    {
      label: "Retail & dining",
      value: "Preview information",
    },
  ],
  opportunities: [
    {
      id: "opportunity-3bhk-001",
      title: "Contemporary 3 BHK Residence",
      configuration: "3 BHK",
      price: "₹2.35 Cr",
      area: "1,850 sq.ft.",
      status: "Preview opportunity",
      context: "Connected property experience",
      href: "/property/pune-kalyani-nagar-001",
    },
    {
      id: "opportunity-2bhk-002",
      title: "Modern 2 BHK Residence",
      configuration: "2 BHK",
      price: "₹1.42 Cr",
      area: "1,220 sq.ft.",
      status: "Preview opportunity",
      context: "Experience-ready inventory card",
    },
    {
      id: "opportunity-4bhk-003",
      title: "Large 4 BHK Residence",
      configuration: "4 BHK",
      price: "₹2.85 Cr",
      area: "2,250 sq.ft.",
      status: "Preview opportunity",
      context: "Experience-ready inventory card",
    },
  ],
  inventorySummary: {
    totalLabel: "Preview opportunities",
    residentialLabel: "Residential discovery",
    commercialLabel:
      "Commercial not represented in this preview",
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

export function getProjectPreview(
  projectId: string,
): ProjectRecord | null {
  if (projectId !== PROJECT_PREVIEW.id) {
    return null;
  }

  return {
    ...PROJECT_PREVIEW,
  };
}
