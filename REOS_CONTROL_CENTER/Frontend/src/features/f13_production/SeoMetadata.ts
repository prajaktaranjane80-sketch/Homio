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
  const normalized = trimmed.startsWith("/") ? trimmed : "/" + trimmed;

  if (
    normalized.startsWith("//") ||
    normalized.includes("?") ||
    normalized.includes("#") ||
    normalized.split("/").includes("..") ||
    normalized.includes("\\")
  ) {
    return "/";
  }

  return normalized;
}

function canonicalUrl(path: string): string | undefined {
  const rawBase =
    process.env.HOMIO_APP_URL?.trim() ||
    process.env.NEXT_PUBLIC_SITE_URL?.trim();

  if (!rawBase) return undefined;

  try {
    const base = new URL(rawBase);

    const isLocalDevelopmentHost = [
      "localhost",
      "127.0.0.1",
      "::1",
    ].includes(base.hostname.toLowerCase());

    if (
      base.username ||
      base.password ||
      base.search ||
      base.hash ||
      base.pathname !== "/" ||
      (process.env.NODE_ENV === "production" &&
        base.protocol !== "https:") ||
      (base.protocol !== "https:" &&
        !(process.env.NODE_ENV !== "production" && isLocalDevelopmentHost))
    ) {
      return undefined;
    }

    return new URL(path, base).toString();
  } catch {
    return undefined;
  }
}

export function createSeoMetadata(
  input: SeoMetadataInput,
): Metadata {
  const title = input.title.trim() || HOMIO_SITE_NAME;
  const description =
    input.description?.trim() || HOMIO_DEFAULT_DESCRIPTION;
  const path = normalizePath(input.path);
  const canonical = canonicalUrl(path);
  const image = input.image?.trim();

  return {
    title,
    description,
    ...(canonical
      ? {
          alternates: {
            canonical,
          },
        }
      : {}),
    robots: input.noIndex
      ? { index: false, follow: false }
      : { index: true, follow: true },
    openGraph: {
      type: "website",
      siteName: HOMIO_SITE_NAME,
      title,
      description,
      ...(canonical ? { url: canonical } : {}),
      ...(image
        ? {
            images: [
              {
                url: image,
                alt: title + " — HOMIO",
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
