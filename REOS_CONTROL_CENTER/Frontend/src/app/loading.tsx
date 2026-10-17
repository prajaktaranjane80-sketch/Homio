
import { LoadingBoundary } from "@/features/f13_production/LoadingBoundary";

export default function Loading() {
  return (
    <main className="page-shell">
      <div className="page-container">
        <LoadingBoundary
          isLoading={true}
          label="Loading HOMIO content"
        >
          {null}
        </LoadingBoundary>
      </div>
    </main>
  );
}
