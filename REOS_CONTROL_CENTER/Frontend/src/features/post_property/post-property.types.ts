import type { AreaUnit, CurrencyCode, MarketId } from "@/features/f12_globalization/market-activation.types";

export type PropertyListingIntent = "sale" | "rent" | "commercial";

export type PropertyOwnership =
  | "owner"
  | "authorized_agent"
  | "developer"
  | "authorized_partner";

export type PropertyAvailability =
  | "available"
  | "under_construction"
  | "not_available"
  | "unknown";

export type PostPropertyStep =
  | "type"
  | "location"
  | "ownership"
  | "details"
  | "media"
  | "documents"
  | "pricing"
  | "availability"
  | "review"
  | "verification"
  | "submit"
  | "status";

export type PropertyDetails = Readonly<{
  title: string;
  description: string;
  propertyType: string;
  bedrooms: string;
  bathrooms: string;
  area: string;
  areaUnit: AreaUnit;
}>;

export type PostPropertyDraft = Readonly<{
  listingIntent?: PropertyListingIntent;
  countryCode?: string;
  marketId?: MarketId;
  locality?: string;
  address?: string;
  ownership?: PropertyOwnership;
  details?: PropertyDetails;
  askingPrice?: string;
  currency?: CurrencyCode;
  availability?: PropertyAvailability;
  availableFrom?: string;
  mediaFileNames?: readonly string[];
  documentFileNames?: readonly string[];
}>;

export type VerificationState =
  | "not_started"
  | "pending"
  | "verified"
  | "rejected"
  | "unavailable";

export type SubmissionState =
  | "draft"
  | "submitted"
  | "in_review"
  | "verified"
  | "rejected"
  | "unavailable";

export type PostPropertySubmissionResult = Readonly<{
  accepted: boolean;
  reference?: string;
  message?: string;
}>;

export type PostPropertyStatusRecord = Readonly<{
  state: SubmissionState;
  reference?: string;
  updatedAt?: string;
  message?: string;
}>;
