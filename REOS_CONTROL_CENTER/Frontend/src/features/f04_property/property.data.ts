import type { PropertyRecord } from "./property.types";

/**
 * F04 experience preview only.
 *
 * This object is not canonical property inventory and must not be treated
 * as authoritative business data. A verified REOS property capability
 * will replace this preview adapter when the integration contract is ready.
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
  status: "Preview / Ready-to-move experience",
  price: "₹2.35 Cr",
  priceContext: "Experience preview value",
  area: "1,850 sq.ft.",
  bedrooms: 3,
  bathrooms: 3,
  parking: "2 covered",
  furnishing: "Semi-furnished",
  possession: "Ready now",
  projectName: "HOMIO Kalyani Residences",
  builderName: "Experience preview",
  description:
    "A HOMIO property-experience preview used to validate the production information hierarchy, media flow, trust treatment and consumer actions before verified REOS property data is connected.",
  verified: false,
  verificationLabel: "Verification pending",
  media: [
    {
      id: "media-01",
      label: "Living spaces",
      type: "image",
    },
    {
      id: "media-02",
      label: "Primary bedroom",
      type: "image",
    },
    {
      id: "media-03",
      label: "Floor plan",
      type: "floor-plan",
    },
    {
      id: "media-04",
      label: "Property walkthrough",
      type: "video",
    },
  ],
  amenities: [
    { label: "Parking", value: "2 covered spaces" },
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
    "Clear 3-bedroom information hierarchy",
    "Structured property decision support",
    "Safe verification treatment",
  ],
  nearby: [
    { label: "Airport", value: "Preview information" },
    { label: "Business district", value: "Preview information" },
    { label: "Schools", value: "Preview information" },
    { label: "Retail & dining", value: "Preview information" },
  ],
};

export function getPropertyPreview(
  propertyId: string,
): PropertyRecord | null {
  if (propertyId !== PROPERTY_PREVIEW.id) {
    return null;
  }

  return {
    ...PROPERTY_PREVIEW,
  };
}
