export type ProjectMedia = {
  id: string;
  label: string;
  type: "image" | "video" | "virtual" | "master-plan";
};

export type ProjectOpportunity = {
  id: string;
  title: string;
  configuration: string;
  price: string;
  area: string;
  status: string;
  context: string;
  href?: string;
};

export type ProjectRelatedItem = {
  id: string;
  name: string;
  location: string;
  highlight: string;
};

export type ProjectAmenity = {
  label: string;
  value: string;
};

export type ProjectNearbyItem = {
  label: string;
  value: string;
};

export type ProjectRecord = {
  id: string;
  name: string;
  shortName: string;
  kind: "project" | "collection";
  kindLabel: string;
  location: string;
  locality: string;
  city: string;
  country: string;
  developerName: string;
  status: string;
  priceFrom: string;
  priceContext: string;
  configurations: string[];
  areaRange: string;
  possession: string;
  collectionName?: string;
  description: string;
  verified: boolean;
  verificationLabel: string;
  media: ProjectMedia[];
  facts: Array<{
    label: string;
    value: string;
  }>;
  amenities: ProjectAmenity[];
  nearby: ProjectNearbyItem[];
  opportunities: ProjectOpportunity[];
  inventorySummary: {
    totalLabel: string;
    residentialLabel: string;
    commercialLabel: string;
    availabilityLabel: string;
  };
  relatedProjects: ProjectRelatedItem[];
};
