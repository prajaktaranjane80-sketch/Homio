import AuthPanel from "@/features/authentication/AuthPanel";

type LoginPageProps = Readonly<{
  searchParams?: Promise<{ error?: string; status?: string }>;
}>;

export const metadata = {
  title: "Sign in",
  robots: { index: false, follow: false },
};

export default async function LoginPage({ searchParams }: LoginPageProps) {
  const params = searchParams ? await searchParams : {};
  return <AuthPanel mode="login" error={params.error} status={params.status} />;
}