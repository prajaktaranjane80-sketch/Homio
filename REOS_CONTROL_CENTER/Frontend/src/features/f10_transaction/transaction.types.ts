export type TransactionViewerRole =
  | "buyer"
  | "seller"
  | "buyer_agent"
  | "seller_agent"
  | "broker"
  | "legal"
  | "finance"
  | "other";

export type StatusTone =
  | "positive"
  | "warning"
  | "danger"
  | "info"
  | "neutral";

export type TransactionStatusCode =
  | "draft"
  | "offer_submitted"
  | "negotiation"
  | "offer_accepted"
  | "due_diligence"
  | "documentation"
  | "financing"
  | "completion_pending"
  | "completed"
  | "cancelled"
  | "on_hold"
  | "unknown";

export type OfferStatusCode =
  | "not_received"
  | "submitted"
  | "under_review"
  | "countered"
  | "accepted"
  | "declined"
  | "withdrawn"
  | "expired"
  | "unknown";

export type DocumentStatusCode =
  | "not_provided"
  | "requested"
  | "uploaded"
  | "under_review"
  | "verified"
  | "rejected"
  | "expired"
  | "not_applicable";

export type MilestoneStatusCode =
  | "upcoming"
  | "in_progress"
  | "completed"
  | "delayed"
  | "blocked";

export type FinancialStatusCode =
  | "not_provided"
  | "not_due"
  | "due"
  | "partially_paid"
  | "paid"
  | "overdue"
  | "on_hold"
  | "unknown";

export type CommissionStatusCode =
  | "not_provided"
  | "not_applicable"
  | "pending"
  | "under_review"
  | "approved"
  | "payable"
  | "paid"
  | "on_hold"
  | "disputed";

export type CompletionStatusCode =
  | "not_started"
  | "in_progress"
  | "awaiting_confirmation"
  | "completed"
  | "blocked"
  | "unknown";

export type TransactionActionState =
  | "available"
  | "pending"
  | "completed"
  | "blocked";

export type TransactionActionCategory =
  | "review"
  | "document"
  | "payment"
  | "communication"
  | "completion"
  | "general";

/**
 * This describes an action supplied by an authorized service.
 * Its UI state is not an authorization decision.
 * The server must authorize the action again when it is invoked.
 */
export type TransactionAction = Readonly<{
  id: string;
  label: string;
  description?: string;
  category: TransactionActionCategory;
  state: TransactionActionState;
  dueAt?: string;
}>;

export type TransactionProperty = Readonly<{
  id: string;
  title: string;
  location: string;
  propertyType?: string;
  imageUrl?: string;
  displayPrice?: string;
  bedrooms?: number;
  bathrooms?: number;
  areaValue?: number;
  areaUnit?: string;
}>;

export type TransactionPartyRole =
  | "buyer"
  | "seller"
  | "buyer_agent"
  | "seller_agent"
  | "broker"
  | "legal"
  | "lender"
  | "other";

export type TransactionParty = Readonly<{
  id: string;
  displayName: string;
  role: TransactionPartyRole;
  organization?: string;
  /**
   * Only provide contact details when they are authorized for this viewer.
   * Do not populate this field with data that should remain private.
   */
  contactLabel?: string;
}>;

export type OfferDetails = Readonly<{
  amount?: number;
  currency?: string;
  status: OfferStatusCode;
  submittedAt?: string;
  expiresAt?: string;
  terms?: readonly Readonly<{
    label: string;
    value: string;
  }>[];
  serviceNote?: string;
}>;

export type NegotiationEntry = Readonly<{
  id: string;
  title: string;
  summary?: string;
  actorLabel?: string;
  status: string;
  updatedAt?: string;
  action?: TransactionAction;
}>;

export type TransactionDocument = Readonly<{
  id: string;
  name: string;
  description?: string;
  status: DocumentStatusCode;
  required: boolean;
  dueAt?: string;
  updatedAt?: string;
  action?: TransactionAction;
}>;

export type TransactionMilestone = Readonly<{
  id: string;
  title: string;
  description?: string;
  status: MilestoneStatusCode;
  targetAt?: string;
  updatedAt?: string;
}>;

export type TransactionFinancialSummary = Readonly<{
  status: FinancialStatusCode;
  currency?: string;
  totalAmount?: number;
  paidToDate?: number;
  balanceRemaining?: number;
  nextPaymentAmount?: number;
  nextPaymentDueAt?: string;
  serviceNote?: string;
}>;

export type CommissionSummary = Readonly<{
  status: CommissionStatusCode;
  amount?: number;
  currency?: string;
  basisLabel?: string;
  payableAt?: string;
  serviceNote?: string;
}>;

export type CompletionItem = Readonly<{
  id: string;
  label: string;
  status: "pending" | "completed" | "blocked";
}>;

export type DealCompletionSummary = Readonly<{
  status: CompletionStatusCode;
  completedAt?: string;
  serviceNote?: string;
  items: readonly CompletionItem[];
}>;

/**
 * Read-only view model. Populate it from an authorized server response.
 * This type does not establish that a transaction exists or that a viewer
 * is authorized to see it.
 */
export type TransactionRecord = Readonly<{
  id: string;
  title: string;
  reference?: string;
  status: TransactionStatusCode;
  updatedAt?: string;
  property: TransactionProperty;
  parties: readonly TransactionParty[];
  offer?: OfferDetails;
  negotiations: readonly NegotiationEntry[];
  documents: readonly TransactionDocument[];
  milestones: readonly TransactionMilestone[];
  financial?: TransactionFinancialSummary;
  commission?: CommissionSummary;
  completion?: DealCompletionSummary;
  nextActions: readonly TransactionAction[];
}>;

export type TransactionActionRequestHandler = (
  action: TransactionAction,
) => void;
