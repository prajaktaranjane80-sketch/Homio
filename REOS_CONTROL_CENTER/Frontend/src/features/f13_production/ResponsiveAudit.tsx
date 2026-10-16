
export const HOMIO_BREAKPOINTS = {
  mobile: 767,
  tablet: 1023,
  desktop: 1439,
  wide: 1440,
} as const;

export type ResponsiveViewport =
  | "mobile"
  | "tablet"
  | "desktop"
  | "wide";

export function getResponsiveViewport(
  width: number,
): ResponsiveViewport {
  if (!Number.isFinite(width) || width < 0) return "mobile";
  if (width <= HOMIO_BREAKPOINTS.mobile) return "mobile";
  if (width <= HOMIO_BREAKPOINTS.tablet) return "tablet";
  if (width <= HOMIO_BREAKPOINTS.desktop) return "desktop";
  return "wide";
}

export function isTouchTargetSizeAcceptable(
  width: number,
  height: number,
): boolean {
  return (
    Number.isFinite(width) &&
    Number.isFinite(height) &&
    width >= 44 &&
    height >= 44
  );
}

export function getHorizontalOverflow(
  documentWidth: number,
  viewportWidth: number,
): number {
  if (
    !Number.isFinite(documentWidth) ||
    !Number.isFinite(viewportWidth)
  ) {
    return 0;
  }

  return Math.max(0, documentWidth - viewportWidth);
}

export interface ResponsiveAuditResult {
  viewport: ResponsiveViewport;
  viewportWidth: number;
  documentWidth: number;
  horizontalOverflow: number;
  hasHorizontalOverflow: boolean;
}

export function auditResponsiveDimensions(
  viewportWidth: number,
  documentWidth: number,
): ResponsiveAuditResult {
  const safeViewport = Math.max(
    0,
    Number.isFinite(viewportWidth) ? viewportWidth : 0,
  );

  const safeDocument = Math.max(
    0,
    Number.isFinite(documentWidth) ? documentWidth : safeViewport,
  );

  const horizontalOverflow = getHorizontalOverflow(
    safeDocument,
    safeViewport,
  );

  return {
    viewport: getResponsiveViewport(safeViewport),
    viewportWidth: safeViewport,
    documentWidth: safeDocument,
    horizontalOverflow,
    hasHorizontalOverflow: horizontalOverflow > 1,
  };
}
