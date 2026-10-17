import Image from "next/image";
import type { ImageProps } from "next/image";

import { getImageQuality } from "./PerformanceConfig";
import { getImagePolicy, isAllowedImageSource } from "./ImagePolicy";

export type PolicyImageProps = Omit<
  ImageProps,
  | "src"
  | "alt"
  | "quality"
  | "sizes"
  | "loading"
  | "fetchPriority"
  | "decoding"
> & {
  src: string;
  alt: string;
  sizes?: string;
  loading?: "eager" | "lazy";
  aboveTheFold?: boolean;
  isLargestContentfulPaintCandidate?: boolean;
};

export function PolicyImage({
  src,
  alt,
  sizes,
  loading,
  aboveTheFold,
  isLargestContentfulPaintCandidate,
  width,
  ...imageProps
}: PolicyImageProps) {
  if (!isAllowedImageSource(src)) {
    if (process.env.NODE_ENV !== "production") {
      console.warn("[HOMIO F13] An image source was blocked by policy.");
    }
    return null;
  }

  const policy = getImagePolicy({
    aboveTheFold,
    isLargestContentfulPaintCandidate,
  });

  const requestedWidth = Number(width ?? 1024);
  const quality = getImageQuality(
    Number.isFinite(requestedWidth) ? requestedWidth : 1024,
  );

  return (
    <Image
      {...imageProps}
      src={src}
      alt={alt}
      width={width}
      sizes={sizes ?? policy.sizes}
      loading={loading ?? policy.loading}
      fetchPriority={policy.fetchPriority}
      decoding={policy.decoding}
      quality={quality}
    />
  );
}
