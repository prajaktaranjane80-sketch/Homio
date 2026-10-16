import type { ReactNode } from "react";

export type ContentLink = Readonly<{
  id: string;
  title: string;
  href: string;
  description: string;
  category?: string;
  updatedAt?: string;
}>;

export type ContentSection = Readonly<{
  id: string;
  title: string;
  body: string;
}>;

export type AdviceArticleRecord = ContentLink & Readonly<{
  category: string;
  readingMinutes?: number;
  publishedAt?: string;
}>;

export type MarketReportRecord = ContentLink & Readonly<{
  marketName: string;
  state: "published" | "preview" | "unavailable";
  sourceName?: string;
  periodLabel?: string;
}>;

export type ContentDocument = Readonly<{
  title: string;
  subtitle?: string;
  updatedAt?: string;
  sourceDisclosure: string;
  sections: readonly ContentSection[];
}>;

export type ContentIndexProps = Readonly<{
  title: string;
  description: string;
  items: readonly ContentLink[];
  emptyMessage?: string;
}>;

export type VideoSource = Readonly<{
  src: string;
  type?: string;
}>;

export type ContentArticleProps = Readonly<{
  title: string;
  summary: string;
  category?: string;
  updatedAt?: string;
  sourceDisclosure: string;
  children?: ReactNode;
}>;
