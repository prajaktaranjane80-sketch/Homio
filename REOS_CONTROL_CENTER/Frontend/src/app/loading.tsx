import { Skeleton } from "@/components/ui/Skeleton";

export default function Loading() {
  return (
    <main className="page-shell" aria-busy="true" aria-live="polite">
      <div className="page-container">
        <div className="loading-stack">
          <Skeleton width="140px" height="14px" />
          <Skeleton width="72%" height="64px" />
          <Skeleton width="58%" height="24px" />
          <div className="loading-grid">
            <Skeleton height="180px" />
            <Skeleton height="180px" />
            <Skeleton height="180px" />
          </div>
        </div>
      </div>
    </main>
  );
}
