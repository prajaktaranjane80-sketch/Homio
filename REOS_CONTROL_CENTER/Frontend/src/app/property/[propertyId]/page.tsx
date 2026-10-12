import type { Metadata } from "next";
import { notFound } from "next/navigation";

import PropertyPage from "@/features/f04_property/PropertyPage";
import { getPropertyPreview } from "@/features/f04_property/property.data";

type PropertyRouteProps = Readonly<{
  params: Promise<{
    propertyId: string;
  }>;
}>;

export async function generateMetadata({
  params,
}: PropertyRouteProps): Promise<Metadata> {
  const { propertyId } = await params;
  const property = getPropertyPreview(propertyId);

  if (!property) {
    return {
      title: "Property unavailable",
      description: "This HOMIO property is currently unavailable.",
      robots: {
        index: false,
        follow: false,
      },
    };
  }

  const title = `${property.shortTitle} — Experience Preview`;
  const description =
    `Experience preview of ${property.propertyType.toLowerCase()} ` +
    `in ${property.location}. This sample record is not verified. ` +
    "Property facts, pricing and availability are not authoritative inventory.";

  return {
    title,
    description,
    robots: {
      index: false,
      follow: true,
    },
    openGraph: {
      title,
      description,
      type: "website",
    },
  };
}

export default async function PropertyRoute({
  params,
}: PropertyRouteProps) {
  const { propertyId } = await params;
  const property = getPropertyPreview(propertyId);

  if (!property) {
    notFound();
  }

  return <PropertyPage property={property} />;
}
