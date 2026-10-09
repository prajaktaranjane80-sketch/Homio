import type { PropertyRecord } from "./property.types";

/**
 * F04 experience preview only.
 * This is not authoritative REOS inventory.
 */
export const PROPERTY_PREVIEW: PropertyRecord = {
  id: "pune-kalyani-nagar-001",
  title: "Contemporary 3 BHK Residence",
  shortTitle: "Contemporary 3 BHK",
  location: "Kalyani Nagar, Pune",
  locality: "Kalyani Nagar",
  city: "Pune",
  country: "India",
  propertyType: "Apartment",
  status: "Ready to move",
  price: "₹2.35 Cr",
  priceContext: "Experience preview value — not verified",
  area: "1,850 sq.ft.",
  bedrooms: 3,
  bathrooms: 3,
  parking: "2 covered",
  furnishing: "Semi-furnished",
  possession: "Preview information",
  projectId: "homio-kalyani-residences-001",
  projectName: "HOMIO Kalyani Residences",
  builderName: "Experience preview",
  description:
    "A HOMIO property-experience preview. Price, availability, ownership and property facts require authoritative verification.",
  verified: false,
  verificationLabel: "Verification pending",
  media: [
    { id: "media-01", label: "Living spaces", type: "image" },
    { id: "media-02", label: "Primary bedroom", type: "image" },
    { id: "media-03", label: "Floor plan", type: "floor-plan" },
    { id: "media-04", label: "Property walkthrough", type: "video" },
  ],
  amenities: [
    { label: "Parking", value: "2 covered spaces — preview" },
    { label: "Lift", value: "Preview information" },
    { label: "Security", value: "Preview information" },
    { label: "Gym", value: "Preview information" },
    { label: "Swimming Pool", value: "Preview information" },
    { label: "Power Backup", value: "Preview information" },
    { label: "Balcony", value: "Preview information" },
    { label: "Clubhouse", value: "Preview information" },
  ],
  highlights: [
    "Connected-location property discovery experience",
    "Structured property information",
    "Property decision-support layout",
    "Verification status displayed explicitly",
  ],
  nearby: [
    { label: "Airport", value: "Preview information" },
    { label: "Business district", value: "Preview information" },
    { label: "Schools", value: "Preview information" },
    { label: "Retail and dining", value: "Preview information" },
  ],
};

const PROPERTY_PREVIEW_VARIANTS: Record<
  string,
  Partial<PropertyRecord>
> = {
  "pune-koregaon-park-002": {
    title: "Refined 4 BHK Urban Villa",
    shortTitle: "Refined 4 BHK Villa",
    location: "Koregaon Park, Pune",
    locality: "Koregaon Park",
    propertyType: "Villa",
    status: "New launch",
    price: "₹4.80 Cr",
    priceContext: "Experience preview value — not verified",
    area: "3,200 sq.ft.",
    bedrooms: 4,
    bathrooms: 4,
    furnishing: "Preview information",
  },
  "pune-baner-003": {
    title: "Modern 2 BHK City Home",
    shortTitle: "Modern 2 BHK Home",
    location: "Baner, Pune",
    locality: "Baner",
    propertyType: "Apartment",
    status: "Under construction",
    price: "₹1.28 Cr",
    priceContext: "Experience preview value — not verified",
    area: "1,220 sq.ft.",
    bedrooms: 2,
    bathrooms: 2,
    furnishing: "Preview information",
  },
  "pune-viman-nagar-004": {
    title: "Premium 3 BHK Residence",
    shortTitle: "Premium 3 BHK",
    location: "Viman Nagar, Pune",
    locality: "Viman Nagar",
    propertyType: "Apartment",
    status: "Ready to move",
    price: "₹1.95 Cr",
    priceContext: "Experience preview value — not verified",
    area: "1,640 sq.ft.",
    bedrooms: 3,
    bathrooms: 3,
    furnishing: "Preview information",
  },
  "pune-wakad-005": {
    title: "Family 3 BHK Smart Home",
    shortTitle: "Family 3 BHK Home",
    location: "Wakad, Pune",
    locality: "Wakad",
    propertyType: "Apartment",
    status: "New launch",
    price: "₹1.12 Cr",
    priceContext: "Experience preview value — not verified",
    area: "1,470 sq.ft.",
    bedrooms: 3,
    bathrooms: 2,
    furnishing: "Preview information",
  },
  "pune-hinjewadi-006": {
    title: "Connected 2 BHK Investment Home",
    shortTitle: "Connected 2 BHK",
    location: "Hinjewadi, Pune",
    locality: "Hinjewadi",
    propertyType: "Apartment",
    status: "Under construction",
    price: "₹89 Lakh",
    priceContext: "Experience preview value — not verified",
    area: "1,060 sq.ft.",
    bedrooms: 2,
    bathrooms: 2,
    furnishing: "Preview information",
  },
  "pune-magarpattacity-007": {
    title: "Executive 3 BHK Residence",
    shortTitle: "Executive 3 BHK",
    location: "Magarpatta City, Pune",
    locality: "Magarpatta City",
    propertyType: "Apartment",
    status: "Ready to move",
    price: "₹1.72 Cr",
    priceContext: "Experience preview value — not verified",
    area: "1,580 sq.ft.",
    bedrooms: 3,
    bathrooms: 3,
    furnishing: "Preview information",
  },
  "pune-aundh-008": {
    title: "Elegant 4 BHK Residence",
    shortTitle: "Elegant 4 BHK",
    location: "Aundh, Pune",
    locality: "Aundh",
    propertyType: "Apartment",
    status: "Ready to move",
    price: "₹2.85 Cr",
    priceContext: "Experience preview value — not verified",
    area: "2,250 sq.ft.",
    bedrooms: 4,
    bathrooms: 4,
    furnishing: "Preview information",
  },
};

export function getPropertyPreview(
  propertyId: string,
): PropertyRecord | null {
  if (propertyId === PROPERTY_PREVIEW.id) {
    return { ...PROPERTY_PREVIEW };
  }

  const variant = PROPERTY_PREVIEW_VARIANTS[propertyId];

  if (!variant) {
    return null;
  }

  const record: PropertyRecord = {
    ...PROPERTY_PREVIEW,
    ...variant,
    id: propertyId,
    projectName: "Experience preview",
    builderName: "Experience preview",
    description:
      "This is a property-experience preview for route and layout validation. Property facts, price and availability are not authoritatively verified.",
    priceContext: "Experience preview value — not verified",
    possession: "Preview information",
    verified: false,
    verificationLabel: "Verification pending",
  };

  // Do not inherit the primary property's project relationship.
  delete record.projectId;
  delete record.projectName;

  return record;
}
