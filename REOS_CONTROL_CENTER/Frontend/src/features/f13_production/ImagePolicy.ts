
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

const ALLOWED_REMOTE_IMAGE_HOSTS = new Set([
  "images.unsplash.com",
]);

export function getImagePolicy(
  options: {
    aboveTheFold?: boolean;
    isLargestContentfulPaintCandidate?: boolean;
  } = {},
): HomioImagePolicy {
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

export function isAllowedImageSource(source: string): boolean {
  const value = source.trim();

  if (!value || value.startsWith("//")) return false;
  if (/[\u0000-\u001f]/.test(value)) return false;

  // Permit safe same-origin absolute paths only.
  if (value.startsWith("/")) {
    return (
      !value.startsWith("/\\") &&
      !value.split("/").includes("..")
    );
  }

  try {
    const url = new URL(value);

    return (
      url.protocol === "https:" &&
      ALLOWED_REMOTE_IMAGE_HOSTS.has(url.hostname.toLowerCase()) &&
      !url.username &&
      !url.password &&
      !url.port
    );
  } catch {
    return false;
  }
}
