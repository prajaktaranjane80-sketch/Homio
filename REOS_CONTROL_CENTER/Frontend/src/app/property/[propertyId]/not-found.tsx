import PropertyUnavailable from "@/features/f04_property/PropertyUnavailable";

export default function PropertyNotFound() {
  return (
    <PropertyUnavailable
      title="We couldn't find this property."
      description="The property reference may be unavailable, expired or not accessible in the current HOMIO experience."
    />
  );
}
