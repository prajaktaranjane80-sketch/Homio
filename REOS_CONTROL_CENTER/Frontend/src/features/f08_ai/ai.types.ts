import type {
  SearchCurrency,
  SearchIntent,
} from "@/features/f03_search/search.types";

export type AIMessageRole = "user" | "workspace";

export type AIConversationMessage = Readonly<{
  id: string;
  role: AIMessageRole;
  content: string;
}>;

export type AIPromptSuggestion = Readonly<{
  id: string;
  title: string;
  description: string;
  prompt: string;
  intent: SearchIntent;
  glyph: string;
}>;

export type AISearchLaunch = Readonly<{
  intent: SearchIntent;
  location: string;
  budget: string;
  currency: SearchCurrency;
  query: string;
}>;
