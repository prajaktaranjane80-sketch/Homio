
import type { Metadata } from "next";
import { cookies } from "next/headers";
import { notFound, redirect } from "next/navigation";

import TransactionShell from "@/features/f10_transaction/TransactionShell";
import {
  SESSION_COOKIE,
  readSessionCookie,
} from "@/lib/auth/oidc";

type TransactionPageProps = Readonly<{
  params: Promise<{
    transactionId: string;
  }>;
}>;

const TRANSACTION_ID_PATTERN =
  /^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$/;

export const metadata: Metadata = {
  title: "Transaction Workspace | HOMIO",
  description:
    "Review transaction progress and authorized next steps in HOMIO.",
  robots: {
    index: false,
    follow: false,
  },
};

export const dynamic = "force-dynamic";

export default async function TransactionPage({
  params,
}: TransactionPageProps) {
  const { transactionId } = await params;

  if (!TRANSACTION_ID_PATTERN.test(transactionId)) {
    notFound();
  }

  const cookieStore = await cookies();
  const session = readSessionCookie(
    cookieStore.get(SESSION_COOKIE)?.value,
  );

  if (!session) {
    const returnTo = `/transaction/${transactionId}`;
    redirect(`/login?returnTo=${encodeURIComponent(returnTo)}`);
  }

  /*
   * The verified transaction-service contract is not connected yet.
   * Do not fetch from an invented endpoint or construct mock transaction data.
   * TransactionShell deliberately displays the safe empty state until an
   * authorized server-side transaction record can be supplied.
   *
   * When integrating the service, authorize this session against this exact
   * transaction on the server before passing a TransactionRecord to the shell.
   */
  return <TransactionShell />;
}
