import type { Metadata } from "next";

export const HOMIO_SITE_NAME = "HOMIO";

export const HOMIO_DEFAULT_DESCRIPTION =
  "Discover homes, rentals, commercial spaces and property projects through HOMIO.";

export interface SeoMetadataInput {
  title: string;
  description?: string;
  path?: string;
  image?: string;
  noIndex?: boolean;
}

function normalizePath(path = "/"): string {
  const trimmed = path.trim();

  if (!trimmed) return "/";
  return trimmed.startsWith("/") ? trimmed : `/${trimmed}`;
}

export function createSeoMetadata(
  input: SeoMetadataInput,
): Metadata {
  const title = input.title.trim() || HOMIO_SITE_NAME;
  const description =
    input.description?.trim() || HOMIO_DEFAULT_DESCRIPTION;
  const path = normalizePath(input.path);
  const image = input.image?.trim();

  return {
    title,
    description,
    alternates: {
      canonical: path,
    },
    robots: input.noIndex
      ? { index: false, follow: false }
      : { index: true, follow: true },
    openGraph: {
      type: "website",
      siteName: HOMIO_SITE_NAME,
      title,
      description,
      url: path,
      ...(image
        ? {
            images: [
              {
                url: image,
                alt: `${title} — HOMIO`,
              },
            ],
          }
        : {}),
    },
    twitter: {
      card: image ? "summary_large_image" : "summary",
      title,
      description,
      ...(image ? { images: [image] } : {}),
    },
  };
}
