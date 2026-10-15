import type { SearchCurrency } from "@/features/f03_search/search.types";

import type {
  ContactPreference,
  EnquiryPurpose,
  EnquiryQualification,
  EnquiryTimeframe,
} from "./enquiry.types";

import type {
  VisitTimeWindow,
  VisitType,
} from "./visit.types";

/**
 * Both flags stay false until their authorized server-side services exist.
 * UI components must not present local drafts as successful submissions.
 */
export const ENQUIRY_SERVICE_CONNECTED = false;
export const VISIT_SCHEDULING_SERVICE_CONNECTED = false;

export const ENQUIRY_PURPOSE_OPTIONS: ReadonlyArray<{
  value: EnquiryPurpose;
  label: string;
}> = [
  { value: "buy", label: "Purchase a property" },
  { value: "rent", label: "Rent a property" },
  { value: "lease", label: "Lease a space" },
  { value: "invest", label: "Explore an investment" },
  { value: "commercial", label: "Commercial property requirement" },
  { value: "general", label: "General property enquiry" },
];

export const CONTACT_PREFERENCE_OPTIONS: ReadonlyArray<{
  value: ContactPreference;
  label: string;
}> = [
  { value: "email", label: "Email" },
  { value: "phone", label: "Phone call" },
  { value: "whatsapp", label: "WhatsApp" },
];

export const ENQUIRY_QUALIFICATION_OPTIONS: ReadonlyArray<{
  value: EnquiryQualification;
  label: string;
}> = [
  { value: "ready", label: "Ready to take the next step" },
  { value: "exploring", label: "Comparing a few options" },
  { value: "investing", label: "Researching investment options" },
  { value: "relocating", label: "Planning a relocation" },
  { value: "researching", label: "Early-stage research" },
];

export const ENQUIRY_TIMEFRAME_OPTIONS: ReadonlyArray<{
  value: EnquiryTimeframe;
  label: string;
}> = [
  { value: "immediately", label: "As soon as practical" },
  { value: "within_30_days", label: "Within 30 days" },
  { value: "within_3_months", label: "Within 3 months" },
  { value: "within_6_months", label: "Within 6 months" },
  { value: "flexible", label: "Flexible timeline" },
];

export const ENQUIRY_CURRENCY_OPTIONS: ReadonlyArray<{
  value: SearchCurrency;
  label: string;
}> = [
  { value: "INR", label: "INR · ₹" },
  { value: "AED", label: "AED" },
  { value: "SGD", label: "SGD" },
  { value: "JPY", label: "JPY · ¥" },
];

export const VISIT_TYPE_OPTIONS: ReadonlyArray<{
  value: VisitType;
  label: string;
}> = [
  { value: "in_person", label: "In-person property visit" },
  { value: "video_call", label: "Video walkthrough request" },
];

export const VISIT_TIME_WINDOWS: ReadonlyArray<{
  value: VisitTimeWindow;
  label: string;
}> = [
  { value: "09:00-11:00", label: "09:00–11:00" },
  { value: "11:00-13:00", label: "11:00–13:00" },
  { value: "13:00-15:00", label: "13:00–15:00" },
  { value: "15:00-17:00", label: "15:00–17:00" },
  { value: "17:00-19:00", label: "17:00–19:00" },
];

export const MIN_VISIT_LEAD_DAYS = 1;
export const MAX_VISIT_LEAD_DAYS = 90;

export const ENQUIRY_SERVICE_NOTICE =
  "Your enquiry has not been sent. The authorized enquiry service is not connected in this preview.";

export const VISIT_SERVICE_NOTICE =
  "Your visit has not been booked. The authorized scheduling service is not connected in this preview.";

export function isValidEmail(value: string): boolean {
  const normalized = value.trim();

  if (normalized.length > 254) {
    return false;
  }

  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalized);
}

/**
 * Supports international numbers without forcing an India-specific format.
 * The form should ask users to include their country calling code.
 */
export function isValidInternationalPhone(value: string): boolean {
  const digits = value.replace(/\D/g, "");

  return digits.length >= 7 && digits.length <= 15;
}

export function isValidVisitDate(
  value: string,
  now: Date = new Date(),
): boolean {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    return false;
  }

  const requestedDate = new Date(`${value}T12:00:00`);
  const parsedYear = requestedDate.getFullYear();
  const parsedMonth = requestedDate.getMonth() + 1;
  const parsedDay = requestedDate.getDate();

  const [year, month, day] = value.split("-").map(Number);

  if (
    parsedYear !== year ||
    parsedMonth !== month ||
    parsedDay !== day
  ) {
    return false;
  }

  const today = new Date(
    now.getFullYear(),
    now.getMonth(),
    now.getDate(),
  );

  const earliest = new Date(today);
  earliest.setDate(
    earliest.getDate() + MIN_VISIT_LEAD_DAYS,
  );

  const latest = new Date(today);
  latest.setDate(
    latest.getDate() + MAX_VISIT_LEAD_DAYS,
  );

  return requestedDate >= earliest && requestedDate <= latest;
}
