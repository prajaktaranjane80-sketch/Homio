import { NextResponse, type NextRequest } from "next/server";

const SECTION_REDIRECTS: Record<string, string> = {
  "/about": "/#why-homio",
  "/ai": "/#homio-ai",
  "/advice": "/#advice",
  "/help": "/#help",
  "/services": "/#services",
  "/tools": "/#tools",
  "/trust": "/#trust",
  "/saved": "/#save-compare",
  "/compare": "/#save-compare",
  "/pro": "/#post-property",
};

const MARKET_CITIES: Record<string, string> = {
  dubai: "Dubai",
  singapore: "Singapore",
  tokyo: "Tokyo",
  london: "London",
  "new-york": "New York",
};

function findSectionRedirect(pathname: string): string | undefined {
  const matchedRoute = Object.keys(SECTION_REDIRECTS).find(
    (route) => pathname === route || pathname.startsWith(`${route}/`),
  );
  return matchedRoute ? SECTION_REDIRECTS[matchedRoute] : undefined;
}

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (pathname === "/market" || pathname.startsWith("/market/")) {
    const citySlug = pathname.split("/").filter(Boolean)[1]?.toLowerCase();
    const destination = new URL("/search", request.url);
    const city = citySlug ? MARKET_CITIES[citySlug] : undefined;
    if (city) destination.searchParams.set("city", city);
    return NextResponse.redirect(destination);
  }

  const sectionDestination = findSectionRedirect(pathname);
  if (sectionDestination) {
    return NextResponse.redirect(new URL(sectionDestination, request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/market/:path*",
    "/about",
    "/about/:path*",
    "/ai/:path*",
    "/advice/:path*",
    "/help/:path*",
    "/services/:path*",
    "/tools/:path*",
    "/trust",
    "/trust/:path*",
    "/saved",
    "/saved/:path*",
    "/compare",
    "/compare/:path*",
    "/pro",
    "/pro/:path*",
  ],
};