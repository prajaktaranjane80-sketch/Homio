import type { PropertyRecord } from "./property.types";

type PropertyPreviewInput = Pick<
  PropertyRecord,
  | "id"
  | "title"
  | "shortTitle"
  | "location"
  | "locality"
  | "city"
  | "country"
  | "propertyType"
  | "price"
  | "area"
  | "bedrooms"
  | "bathrooms"
> &
  Partial<
    Pick<
      PropertyRecord,
      | "status"
      | "priceContext"
      | "parking"
      | "furnishing"
      | "possession"
      | "projectId"
      | "projectName"
      | "builderName"
      | "description"
      | "verificationLabel"
      | "amenities"
      | "highlights"
      | "nearby"
    >
  >;

function createPropertyPreview(
  input: PropertyPreviewInput,
): PropertyRecord {
  return {
    ...input,

    status:
      input.status ?? "Experience preview — not verified",

    priceContext:
      input.priceContext ??
      "Experience preview only. Pricing is not authoritative REOS inventory.",

    parking: input.parking ?? "Preview information",
    furnishing: input.furnishing ?? "Preview information",
    possession: input.possession ?? "Preview information",

    description:
      input.description ??
      "This HOMIO property is an experience preview. Property facts, pricing, availability and verification must be confirmed through authoritative REOS capabilities.",

    verified: false,

    verificationLabel:
      input.verificationLabel ??
      "Verification pending — preview only",

    media: [
      {
        id: `${input.id}-image`,
        label: "Property image preview",
        type: "image",
      },
      {
        id: `${input.id}-floor-plan`,
        label: "Floor plan preview",
        type: "floor-plan",
      },
      {
        id: `${input.id}-walkthrough`,
        label: "Walkthrough preview",
        type: "video",
      },
    ],

    amenities:
      input.amenities ?? [
        {
          label: "Amenities",
          value: "Preview information",
        },
      ],

    highlights:
      input.highlights ?? [
        "Experience preview",
        "Verification pending",
      ],

    nearby:
      input.nearby ?? [
        {
          label: "Location context",
          value: `${input.locality}, ${input.city}`,
        },
      ],
  };
}

const PROPERTY_PREVIEW_VARIANTS: Record<string, PropertyRecord> = {
  // Existing homepage preview properties

  "skyline-residence": createPropertyPreview({
    id: "skyline-residence",
    title: "Skyline Residence",
    shortTitle: "Skyline Residence",
    location: "Dubai Marina, Dubai",
    locality: "Dubai Marina",
    city: "Dubai",
    country: "United Arab Emirates",
    propertyType: "Apartment",
    status: "Experience preview — not verified",
    price: "AED 3.25M",
    area: "1,985 sq.ft.",
    bedrooms: 3,
    bathrooms: 2,
  }),

  "central-park-residence": createPropertyPreview({
    id: "central-park-residence",
    title: "Central Park Residence",
    shortTitle: "Central Park Residence",
    location: "Downtown Dubai",
    locality: "Downtown Dubai",
    city: "Dubai",
    country: "United Arab Emirates",
    propertyType: "Apartment",
    status: "Experience preview — not verified",
    price: "AED 2.10M",
    area: "1,240 sq.ft.",
    bedrooms: 2,
    bathrooms: 2,
  }),

  "harbour-view-home": createPropertyPreview({
    id: "harbour-view-home",
    title: "Harbour View Home",
    shortTitle: "Harbour View Home",
    location: "Singapore",
    locality: "Singapore",
    city: "Singapore",
    country: "Singapore",
    propertyType: "Residence",
    status: "Experience preview — not verified",
    price: "SGD 2.85M",
    area: "1,650 sq.ft.",
    bedrooms: 3,
    bathrooms: 2,
  }),

  "modern-city-residence": createPropertyPreview({
    id: "modern-city-residence",
    title: "Modern City Residence",
    shortTitle: "Modern City Residence",
    location: "Jumeirah Village Circle, Dubai",
    locality: "Jumeirah Village Circle",
    city: "Dubai",
    country: "United Arab Emirates",
    propertyType: "Apartment",
    status: "Owner-origin concept — not verified",
    price: "AED 1.35M",
    area: "1,180 sq.ft.",
    bedrooms: 2,
    bathrooms: 2,
  }),

  "parkside-family-home": createPropertyPreview({
    id: "parkside-family-home",
    title: "Parkside Family Home",
    shortTitle: "Parkside Family Home",
    location: "Singapore",
    locality: "Singapore",
    city: "Singapore",
    country: "Singapore",
    propertyType: "Residence",
    status: "Owner-origin concept — not verified",
    price: "SGD 2.20M",
    area: "1,540 sq.ft.",
    bedrooms: 3,
    bathrooms: 2,
  }),

  "prime-urban-apartment": createPropertyPreview({
    id: "prime-urban-apartment",
    title: "Prime Urban Apartment",
    shortTitle: "Prime Urban Apartment",
    location: "Minato, Tokyo",
    locality: "Minato",
    city: "Tokyo",
    country: "Japan",
    propertyType: "Apartment",
    status: "Owner-origin concept — not verified",
    price: "JPY 128M",
    area: "890 sq.ft.",
    bedrooms: 2,
    bathrooms: 1,
  }),

  "palm-view-residence": createPropertyPreview({
    id: "palm-view-residence",
    title: "Palm View Residence",
    shortTitle: "Palm View Residence",
    location: "Palm Jumeirah, Dubai",
    locality: "Palm Jumeirah",
    city: "Dubai",
    country: "United Arab Emirates",
    propertyType: "Villa",
    status: "Trust-signal concept — not verified",
    price: "AED 8.90M",
    area: "Preview information",
    bedrooms: 4,
    bathrooms: 4,
  }),

  "central-garden-residence": createPropertyPreview({
    id: "central-garden-residence",
    title: "Central Garden Residence",
    shortTitle: "Central Garden Residence",
    location: "Bukit Timah, Singapore",
    locality: "Bukit Timah",
    city: "Singapore",
    country: "Singapore",
    propertyType: "Residence",
    status: "Trust-signal concept — not verified",
    price: "SGD 3.40M",
    area: "Preview information",
    bedrooms: 3,
    bathrooms: 2,
  }),

  "prime-metropolitan-home": createPropertyPreview({
    id: "prime-metropolitan-home",
    title: "Prime Metropolitan Home",
    shortTitle: "Prime Metropolitan Home",
    location: "Shibuya, Tokyo",
    locality: "Shibuya",
    city: "Tokyo",
    country: "Japan",
    propertyType: "Apartment",
    status: "Trust-signal concept — not verified",
    price: "JPY 145M",
    area: "Preview information",
    bedrooms: 2,
    bathrooms: 1,
  }),

  // F03 Search preview IDs — must resolve through F04

  "pune-kalyani-nagar-001": createPropertyPreview({
    id: "pune-kalyani-nagar-001",
    title: "Contemporary 3 BHK Residence",
    shortTitle: "Contemporary 3 BHK Residence",
    location: "Kalyani Nagar, Pune",
    locality: "Kalyani Nagar",
    city: "Pune",
    country: "India",
    propertyType: "Apartment",
    price: "₹2.35 Cr",
    area: "1,850 sq.ft.",
    bedrooms: 3,
    bathrooms: 3,
    projectName: "HOMIO Kalyani Residences",
    projectId: "homio-kalyani-residences-001",
    status: "Ready to move — preview only",
  }),

  "pune-koregaon-park-002": createPropertyPreview({
    id: "pune-koregaon-park-002",
    title: "Refined 4 BHK Urban Villa",
    shortTitle: "Refined 4 BHK Urban Villa",
    location: "Koregaon Park, Pune",
    locality: "Koregaon Park",
    city: "Pune",
    country: "India",
    propertyType: "Villa",
    price: "₹4.80 Cr",
    area: "3,200 sq.ft.",
    bedrooms: 4,
    bathrooms: 4,
    projectName: "Parkside Villas",
    status: "New launch — preview only",
  }),

  "pune-baner-003": createPropertyPreview({
    id: "pune-baner-003",
    title: "Modern 2 BHK City Home",
    shortTitle: "Modern 2 BHK City Home",
    location: "Baner, Pune",
    locality: "Baner",
    city: "Pune",
    country: "India",
    propertyType: "Apartment",
    price: "₹1.28 Cr",
    area: "1,220 sq.ft.",
    bedrooms: 2,
    bathrooms: 2,
    projectName: "Baner Heights",
    status: "Under construction — preview only",
  }),

  "pune-viman-nagar-004": createPropertyPreview({
    id: "pune-viman-nagar-004",
    title: "Premium 3 BHK Residence",
    shortTitle: "Premium 3 BHK Residence",
    location: "Viman Nagar, Pune",
    locality: "Viman Nagar",
    city: "Pune",
    country: "India",
    propertyType: "Apartment",
    price: "₹1.95 Cr",
    area: "1,640 sq.ft.",
    bedrooms: 3,
    bathrooms: 3,
    projectName: "Skyline Viman",
    status: "Ready to move — preview only",
  }),

  "pune-wakad-005": createPropertyPreview({
    id: "pune-wakad-005",
    title: "Family 3 BHK Smart Home",
    shortTitle: "Family 3 BHK Smart Home",
    location: "Wakad, Pune",
    locality: "Wakad",
    city: "Pune",
    country: "India",
    propertyType: "Apartment",
    price: "₹1.12 Cr",
    area: "1,470 sq.ft.",
    bedrooms: 3,
    bathrooms: 2,
    projectName: "Westline Homes",
    status: "New launch — preview only",
  }),

  "pune-hinjewadi-006": createPropertyPreview({
    id: "pune-hinjewadi-006",
    title: "Connected 2 BHK Investment Home",
    shortTitle: "Connected 2 BHK Investment Home",
    location: "Hinjewadi, Pune",
    locality: "Hinjewadi",
    city: "Pune",
    country: "India",
    propertyType: "Apartment",
    price: "₹89 Lakh",
    area: "1,060 sq.ft.",
    bedrooms: 2,
    bathrooms: 2,
    projectName: "Hinjewadi Central",
    status: "Under construction — preview only",
  }),

  "pune-magarpattacity-007": createPropertyPreview({
    id: "pune-magarpattacity-007",
    title: "Executive 3 BHK Residence",
    shortTitle: "Executive 3 BHK Residence",
    location: "Magarpatta City, Pune",
    locality: "Magarpatta City",
    city: "Pune",
    country: "India",
    propertyType: "Apartment",
    price: "₹1.72 Cr",
    area: "1,580 sq.ft.",
    bedrooms: 3,
    bathrooms: 3,
    projectName: "City Park Residences",
    status: "Ready to move — preview only",
  }),

  "pune-aundh-008": createPropertyPreview({
    id: "pune-aundh-008",
    title: "Elegant 4 BHK Residence",
    shortTitle: "Elegant 4 BHK Residence",
    location: "Aundh, Pune",
    locality: "Aundh",
    city: "Pune",
    country: "India",
    propertyType: "Apartment",
    price: "₹2.85 Cr",
    area: "2,250 sq.ft.",
    bedrooms: 4,
    bathrooms: 4,
    projectName: "Aundh Grand",
    status: "Ready to move — preview only",
  }),

  // Homepage Rental preview IDs — must resolve through F04

  "furnished-city-apartment": createPropertyPreview({
    id: "furnished-city-apartment",
    title: "Furnished City Apartment",
    shortTitle: "Furnished City Apartment",
    location: "Downtown Dubai",
    locality: "Downtown Dubai",
    city: "Dubai",
    country: "United Arab Emirates",
    propertyType: "Apartment",
    price: "AED 12,500 / month",
    area: "Preview information",
    bedrooms: 2,
    bathrooms: 1,
    furnishing: "Furnished — preview only",
    status: "Rental preview — not verified",
    priceContext: "Indicative monthly rent shown for experience preview only.",
  }),

  "marina-lifestyle-home": createPropertyPreview({
    id: "marina-lifestyle-home",
    title: "Marina Lifestyle Home",
    shortTitle: "Marina Lifestyle Home",
    location: "Dubai Marina",
    locality: "Dubai Marina",
    city: "Dubai",
    country: "United Arab Emirates",
    propertyType: "Apartment",
    price: "AED 8,500 / month",
    area: "Preview information",
    bedrooms: 1,
    bathrooms: 1,
    furnishing: "Furnished — preview only",
    status: "Rental preview — not verified",
    priceContext: "Indicative monthly rent shown for experience preview only.",
  }),

  "central-singapore-residence": createPropertyPreview({
    id: "central-singapore-residence",
    title: "Central Singapore Residence",
    shortTitle: "Central Singapore Residence",
    location: "Orchard, Singapore",
    locality: "Orchard",
    city: "Singapore",
    country: "Singapore",
    propertyType: "Residence",
    price: "SGD 7,800 / month",
    area: "Preview information",
    bedrooms: 2,
    bathrooms: 1,
    possession: "Long term — preview only",
    status: "Rental preview — not verified",
    priceContext: "Indicative monthly rent shown for experience preview only.",
  }),
};

export function getPropertyPreview(
  propertyId: string,
): PropertyRecord | null {
  const property = PROPERTY_PREVIEW_VARIANTS[propertyId];

  if (!property) {
    return null;
  }

  return {
    ...property,
    media: property.media.map((item) => ({ ...item })),
    amenities: property.amenities.map((item) => ({ ...item })),
    highlights: [...property.highlights],
    nearby: property.nearby.map((item) => ({ ...item })),
  };
}
