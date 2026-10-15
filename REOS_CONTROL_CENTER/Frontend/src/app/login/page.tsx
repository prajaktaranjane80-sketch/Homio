
import AuthPanel from "@/features/authentication/AuthPanel";
import { safeReturnTo } from "@/lib/auth/oidc";

type LoginPageProps = Readonly<{
  searchParams?: Promise<{
    error?: string;
    status?: string;
    returnTo?: string;
  }>;
}>;

export const metadata = {
  title: "Sign in",
  robots: { index: false, follow: false },
};

export default async function LoginPage({
  searchParams,
}: LoginPageProps) {
  const params = searchParams ? await searchParams : {};
  const returnTo = safeReturnTo(params.returnTo);

  return (
    <AuthPanel
      mode="login"
      error={params.error}
      status={params.status}
      returnTo={returnTo}
    />
  );
}
