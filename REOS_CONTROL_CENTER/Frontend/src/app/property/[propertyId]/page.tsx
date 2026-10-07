import { notFound } from "next/navigation";

import PropertyPage from "@/features/f04_property/PropertyPage";
import { getPropertyPreview } from "@/features/f04_property/property.data";

type PropertyRouteProps = Readonly<{
  params: Promise<{
    propertyId: string;
  }>;
}>;

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
