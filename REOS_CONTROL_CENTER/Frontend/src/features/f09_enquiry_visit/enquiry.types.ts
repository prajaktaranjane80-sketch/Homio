export type EnquiryTargetKind =
  | "property"
  | "project"
  | "general";

export type EnquiryPurpose =
  | "buy"
  | "rent"
  | "lease"
  | "invest"
  | "commercial"
  | "general";

export type ContactPreference =
  | "email"
  | "phone"
  | "whatsapp";

export type EnquiryQualification =
  | "ready"
  | "exploring"
  | "investing"
  | "relocating"
  | "researching";

export type EnquiryTimeframe =
  | "immediately"
  | "within_30_days"
  | "within_3_months"
  | "within_6_months"
  | "flexible";

export type EnquiryStatus =
  | "draft"
  | "ready_to_submit"
  | "submitted"
  | "acknowledged"
  | "in_progress"
  | "responded"
  | "closed"
  | "submission_unavailable";

export type EnquiryTarget = Readonly<{
  kind: EnquiryTargetKind;
  id?: string;
  title?: string;
  location?: string;
  href?: string;
}>;

/**
 * Form draft only. This contains personal data and must not be written to
 * sessionStorage, localStorage, URLs, logs or analytics.
 */
export type EnquiryDraft = Readonly<{
  target: EnquiryTarget;
  purpose: EnquiryPurpose;
  fullName: string;
  email: string;
  phone: string;
  contactPreference: ContactPreference;
  qualification: EnquiryQualification;
  timeframe: EnquiryTimeframe;
  budgetAmount: string;
  budgetCurrency: string;
  message: string;
  consentToContact: boolean;
  consentToMarketing: boolean;
}>;

/**
 * The client may prepare a draft, but only a trusted server response may
 * produce submitted/acknowledged/in-progress states or a reference number.
 */
export type EnquiryStatusSnapshot = Readonly<{
  status: EnquiryStatus;
  updatedAt?: string;
  reference?: string;
  source: "local_preview" | "authorized_service";
  message: string;
}>;

export type EnquiryHistoryItem = Readonly<{
  id: string;
  target: EnquiryTarget;
  status: EnquiryStatus;
  createdAt: string;
  updatedAt?: string;
  reference: string;
  source: "authorized_service";
}>;

export type EnquiryValidationErrors = Partial<
  Record<
    | "fullName"
    | "email"
    | "phone"
    | "purpose"
    | "message"
    | "consentToContact"
    | "general",
    string
  >
>;
