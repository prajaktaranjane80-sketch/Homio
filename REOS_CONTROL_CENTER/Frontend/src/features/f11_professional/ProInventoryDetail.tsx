
import ProUnavailable from "./ProUnavailable";
import ProWorkspace from "./ProWorkspace";

type ProInventoryDetailProps = Readonly<{
  recordId: string;
}>;

const INVENTORY_ID_PATTERN =
  /^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$/;

export default function ProInventoryDetail({
  recordId,
}: ProInventoryDetailProps) {
  const validReference = INVENTORY_ID_PATTERN.test(recordId);

  return (
    <ProWorkspace section="inventory-detail">
      <ProUnavailable
        section="inventory-detail"
        capabilityKey="inventory"
        title={
          validReference
            ? "Inventory record access is not available"
            : "This inventory reference is invalid"
        }
        description={
          validReference
            ? "The requested reference has not been loaded. The server must authorize access to this exact record before any property details are returned."
            : "The supplied inventory reference does not match the accepted identifier format."
        }
        detail="A valid reference is not proof of ownership or permission. No property details or edit actions are exposed by this preview."
      />
    </ProWorkspace>
  );
}
