import type { PropertyRecord } from "./property.types";

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
  priceContext: "Indicative property value",
  area: "1,850 sq.ft.",
  bedrooms: 3,
  bathrooms: 3,
  parking: "2 covered",
  furnishing: "Semi-furnished",
  possession: "Ready now",
  projectName: "HOMIO Kalyani Residences",
  builderName: "Authorized project partner",
  description:
    "A refined urban residence designed for buyers who want a connected Pune location, generous living areas and a considered everyday lifestyle.",
  verified: true,
  verificationLabel: "HOMIO Verified information",
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
    { label: "Lift", value: "Available" },
    { label: "Security", value: "24/7" },
    { label: "Gym", value: "Residents' gym" },
    { label: "Swimming Pool", value: "Available" },
    { label: "Power Backup", value: "Full common-area backup" },
    { label: "Balcony", value: "Yes" },
    { label: "Clubhouse", value: "Available" },
  ],
  highlights: [
    "Connected to major Pune business and lifestyle districts",
    "Ready-to-move positioning",
    "Large 3-bedroom format",
    "HOMIO-verified presentation layer",
  ],
  nearby: [
    { label: "Airport", value: "Approx. 15 min" },
    { label: "Business district", value: "Approx. 10 min" },
    { label: "Schools", value: "Multiple nearby options" },
    { label: "Retail & dining", value: "Immediate locality access" },
  ],
};

export function getPropertyPreview(
  propertyId: string,
): PropertyRecord {
  return {
    ...PROPERTY_PREVIEW,
    id: propertyId || PROPERTY_PREVIEW.id,
  };
}
