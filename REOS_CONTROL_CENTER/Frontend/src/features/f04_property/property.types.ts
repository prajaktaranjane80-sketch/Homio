export type PropertyAmenity = {
  label: string;
  value: string;
};

export type PropertyMedia = {
  id: string;
  label: string;
  type: "image" | "floor-plan" | "video" | "virtual";
};

export type PropertyRecord = {
  id: string;
  title: string;
  shortTitle: string;
  location: string;
  locality: string;
  city: string;
  country: string;
  propertyType: string;
  status: string;
  price: string;
  priceContext: string;
  area: string;
  bedrooms: number;
  bathrooms: number;
  parking: string;
  furnishing: string;
  possession: string;
  projectId?: string;
  projectName?: string;
  builderName?: string;
  description: string;
  verified: boolean;
  verificationLabel: string;
  media: PropertyMedia[];
  amenities: PropertyAmenity[];
  highlights: string[];
  nearby: Array<{
    label: string;
    value: string;
  }>;
};
