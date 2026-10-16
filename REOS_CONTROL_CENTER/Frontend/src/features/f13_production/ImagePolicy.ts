export interface HomioImagePolicy {
  loading: "eager" | "lazy";
  fetchPriority: "high" | "auto" | "low";
  decoding: "async" | "sync" | "auto";
  sizes: string;
}

export const HOMIO_CARD_IMAGE_SIZES =
  "(max-width: 640px) 100vw, " +
  "(max-width: 1024px) 50vw, " +
  "(max-width: 1440px) 33vw, 420px";

export function getImagePolicy(options: {
  aboveTheFold?: boolean;
  isLargestContentfulPaintCandidate?: boolean;
} = {}): HomioImagePolicy {
  const critical = Boolean(
    options.aboveTheFold ||
      options.isLargestContentfulPaintCandidate,
  );

  return {
    loading: critical ? "eager" : "lazy",
    fetchPriority: options.isLargestContentfulPaintCandidate
      ? "high"
      : "auto",
    decoding: "async",
    sizes: HOMIO_CARD_IMAGE_SIZES,
  };
}

export function isAllowedImageSource(
  source: string,
): boolean {
  const value = source.trim();

  if (!value) return false;

  // Allow same-origin absolute paths, but not protocol-relative URLs.
  if (value.startsWith("/") && !value.startsWith("//")) {
    return true;
  }

  try {
    const url = new URL(value);
    return (
      url.protocol === "https:" ||
      url.protocol === "http:"
    );
  } catch {
    return false;
  }
}
