import Link from "next/link";

import { ErrorState } from "@/components/ui/ErrorState";

export default function NotFound() {
  return (
    <main className="page-shell">
      <div className="page-container page-container--narrow">
        <ErrorState
          title="Page not found"
          description="The requested HOMIO experience does not exist at this route."
          action={
            <Link className="button button--secondary" href="/">
              Return home
            </Link>
          }
        />
      </div>
    </main>
  );
}
