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
      title: "Property unavailable | HOMIO",
      description:
        "This HOMIO property is currently unavailable.",
      robots: {
        index: false,
        follow: false,
      },
    };
  }

  return {
    title: `${property.shortTitle} | HOMIO`,
    description:
      `${property.propertyType} in ${property.location}. ` +
      `${property.bedrooms} BHK, ${property.area}. ` +
      "Explore the property on HOMIO.",
    alternates: {
      canonical: `/property/${property.id}`,
    },
    openGraph: {
      title: `${property.shortTitle} | HOMIO`,
      description:
        `${property.propertyType} in ${property.location}. ` +
        "Explore the property on HOMIO.",
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
