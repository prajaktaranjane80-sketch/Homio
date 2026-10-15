import type {
  ContactPreference,
  EnquiryTarget,
} from "./enquiry.types";

export type VisitType =
  | "in_person"
  | "video_call";

export type VisitTimeWindow =
  | "09:00-11:00"
  | "11:00-13:00"
  | "13:00-15:00"
  | "15:00-17:00"
  | "17:00-19:00";

export type VisitStatus =
  | "draft"
  | "ready_to_submit"
  | "requested"
  | "proposed"
  | "confirmed"
  | "reschedule_requested"
  | "cancel_requested"
  | "cancelled"
  | "completed"
  | "declined"
  | "submission_unavailable";

export type VisitDraft = Readonly<{
  target: EnquiryTarget;
  visitType: VisitType;
  preferredDate: string;
  preferredTimeWindow: VisitTimeWindow;
  timeZone: string;
  attendeeCount: number;
  fullName: string;
  email: string;
  phone: string;
  contactPreference: ContactPreference;
  accessibilityNeeds: string;
  notes: string;
  consentToContact: boolean;
}>;

export type VisitStatusSnapshot = Readonly<{
  status: VisitStatus;
  updatedAt?: string;
  reference?: string;
  confirmedAt?: string;
  confirmedDateTime?: string;
  timeZone?: string;
  source: "local_preview" | "authorized_service";
  message: string;
}>;

export type VisitHistoryItem = Readonly<{
  id: string;
  target: EnquiryTarget;
  status: VisitStatus;
  preferredDate: string;
  timeZone: string;
  reference: string;
  updatedAt?: string;
  source: "authorized_service";
}>;

export type VisitAction =
  | "reschedule"
  | "cancel";

export type VisitActionDraft = Readonly<{
  reference: string;
  action: VisitAction;
  reason: string;
  preferredDate?: string;
  preferredTimeWindow?: VisitTimeWindow;
  timeZone?: string;
}>;

export type VisitValidationErrors = Partial<
  Record<
    | "preferredDate"
    | "preferredTimeWindow"
    | "timeZone"
    | "fullName"
    | "email"
    | "phone"
    | "consentToContact"
    | "general",
    string
  >
>;
