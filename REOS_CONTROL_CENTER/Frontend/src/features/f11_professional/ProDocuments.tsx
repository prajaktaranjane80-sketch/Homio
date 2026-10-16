
import ProUnavailable from "./ProUnavailable";
import ProWorkspace from "./ProWorkspace";

export default function ProDocuments() {
  return (
    <ProWorkspace section="documents">
      <ProUnavailable
        section="documents"
        capabilityKey="documents"
        title="Secure documents need verified access"
        description="Document metadata, downloads, review states and signatures must be protected by server-side authorization for each document and operation."
        detail="No private documents or fabricated verification badges are presented. Document contents must not be exposed through public URLs or client-only permission checks."
      />
    </ProWorkspace>
  );
}
