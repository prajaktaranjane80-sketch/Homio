import type {
  CommissionStatusCode,
  CompletionStatusCode,
  DocumentStatusCode,
  FinancialStatusCode,
  MilestoneStatusCode,
  OfferStatusCode,
  StatusTone,
  TransactionPartyRole,
  TransactionStatusCode,
} from "./transaction.types";

export type StatusMeta = Readonly<{
  label: string;
  tone: StatusTone;
  description?: string;
}>;

export const TRANSACTION_STATUS_META: Record<
  TransactionStatusCode,
  StatusMeta
> = {
  draft: { label: "Draft", tone: "neutral" },
  offer_submitted: { label: "Offer submitted", tone: "info" },
  negotiation: { label: "In negotiation", tone: "info" },
  offer_accepted: { label: "Offer accepted", tone: "positive" },
  due_diligence: { label: "Due diligence", tone: "info" },
  documentation: { label: "Documentation", tone: "info" },
  financing: { label: "Financing", tone: "warning" },
  completion_pending: { label: "Completion pending", tone: "warning" },
  completed: { label: "Completed", tone: "positive" },
  cancelled: { label: "Cancelled", tone: "danger" },
  on_hold: { label: "On hold", tone: "warning" },
  unknown: { label: "Status unavailable", tone: "neutral" },
};

export const OFFER_STATUS_META: Record<OfferStatusCode, StatusMeta> = {
  not_received: { label: "Not received", tone: "neutral" },
  submitted: { label: "Submitted", tone: "info" },
  under_review: { label: "Under review", tone: "info" },
  countered: { label: "Counteroffer", tone: "warning" },
  accepted: { label: "Accepted", tone: "positive" },
  declined: { label: "Declined", tone: "danger" },
  withdrawn: { label: "Withdrawn", tone: "neutral" },
  expired: { label: "Expired", tone: "warning" },
  unknown: { label: "Status unavailable", tone: "neutral" },
};

export const DOCUMENT_STATUS_META: Record<
  DocumentStatusCode,
  StatusMeta
> = {
  not_provided: { label: "Not provided", tone: "neutral" },
  requested: { label: "Requested", tone: "warning" },
  uploaded: { label: "Uploaded", tone: "info" },
  under_review: { label: "Under review", tone: "info" },
  verified: { label: "Verified", tone: "positive" },
  rejected: { label: "Needs attention", tone: "danger" },
  expired: { label: "Expired", tone: "warning" },
  not_applicable: { label: "Not applicable", tone: "neutral" },
};

export const MILESTONE_STATUS_META: Record<
  MilestoneStatusCode,
  StatusMeta
> = {
  upcoming: { label: "Upcoming", tone: "neutral" },
  in_progress: { label: "In progress", tone: "info" },
  completed: { label: "Completed", tone: "positive" },
  delayed: { label: "Delayed", tone: "warning" },
  blocked: { label: "Blocked", tone: "danger" },
};

export const FINANCIAL_STATUS_META: Record<
  FinancialStatusCode,
  StatusMeta
> = {
  not_provided: { label: "Not provided", tone: "neutral" },
  not_due: { label: "Not yet due", tone: "info" },
  due: { label: "Payment due", tone: "warning" },
  partially_paid: { label: "Partially paid", tone: "warning" },
  paid: { label: "Paid", tone: "positive" },
  overdue: { label: "Overdue", tone: "danger" },
  on_hold: { label: "On hold", tone: "warning" },
  unknown: { label: "Status unavailable", tone: "neutral" },
};

export const COMMISSION_STATUS_META: Record<
  CommissionStatusCode,
  StatusMeta
> = {
  not_provided: { label: "Not provided", tone: "neutral" },
  not_applicable: { label: "Not applicable", tone: "neutral" },
  pending: { label: "Pending", tone: "info" },
  under_review: { label: "Under review", tone: "info" },
  approved: { label: "Approved", tone: "positive" },
  payable: { label: "Payable", tone: "warning" },
  paid: { label: "Paid", tone: "positive" },
  on_hold: { label: "On hold", tone: "warning" },
  disputed: { label: "Disputed", tone: "danger" },
};

export const COMPLETION_STATUS_META: Record<
  CompletionStatusCode,
  StatusMeta
> = {
  not_started: { label: "Not started", tone: "neutral" },
  in_progress: { label: "In progress", tone: "info" },
  awaiting_confirmation: {
    label: "Awaiting confirmation",
    tone: "warning",
  },
  completed: { label: "Completed", tone: "positive" },
  blocked: { label: "Blocked", tone: "danger" },
  unknown: { label: "Status unavailable", tone: "neutral" },
};

export const PARTY_ROLE_LABELS: Record<TransactionPartyRole, string> = {
  buyer: "Buyer",
  seller: "Seller",
  buyer_agent: "Buyer's representative",
  seller_agent: "Seller's representative",
  broker: "Broker",
  legal: "Legal representative",
  lender: "Lender",
  other: "Participant",
};

export const TONE_CLASS_KEY: Record<StatusTone, string> = {
  positive: "tonePositive",
  warning: "toneWarning",
  danger: "toneDanger",
  info: "toneInfo",
  neutral: "toneNeutral",
};

export function formatCurrency(
  amount?: number,
  currency?: string,
): string {
  if (amount === undefined || !Number.isFinite(amount)) {
    return "Not provided";
  }

  if (!currency || !/^[A-Z]{3}$/.test(currency)) {
    return `${amount.toLocaleString("en")} · currency not supplied`;
  }

  try {
    return new Intl.NumberFormat("en", {
      style: "currency",
      currency,
      maximumFractionDigits: 2,
    }).format(amount);
  } catch {
    return `${currency} ${amount.toLocaleString("en")}`;
  }
}

export function formatDate(value?: string): string {
  if (!value) return "Date not supplied";

  const parsed = new Date(value);

  if (Number.isNaN(parsed.getTime())) {
    return "Date not supplied";
  }

  return new Intl.DateTimeFormat("en", {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(parsed);
}

export function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);

  if (parts.length === 0) return "—";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();

  return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
}

export function humanizeCode(value: string): string {
  return value
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
