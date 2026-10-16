export const HOMIO_PERFORMANCE_CONFIG = {
  imageSizes: [320, 480, 640, 768, 1024, 1280, 1600, 1920],
  imageQualities: [60, 75, 85],
  lazyLoadBelowFoldImages: true,
  reserveImageAspectRatio: true,
  respectReducedMotion: true,
  avoidAutoplayingMediaWithSound: true,
  deferNonCriticalThirdPartyScripts: true,
} as const;

export const HOMIO_CACHE_POLICY = {
  staticAssets: "public, max-age=31536000, immutable",
  html: "no-cache",
  privateUserData: "private, no-store",
} as const;

export function shouldReduceMotion(
  prefersReducedMotion: boolean,
): boolean {
  return prefersReducedMotion;
}

export function getImageQuality(
  width: number,
): 60 | 75 | 85 {
  if (!Number.isFinite(width) || width <= 640) return 60;
  if (width <= 1280) return 75;

  return 85;
}
