import AuthPanel from "@/features/authentication/AuthPanel";

type SignupPageProps = Readonly<{
  searchParams?: Promise<{ error?: string }>;
}>;

export const metadata = {
  title: "Create account",
  robots: { index: false, follow: false },
};

export default async function SignupPage({ searchParams }: SignupPageProps) {
  const params = searchParams ? await searchParams : {};
  return <AuthPanel mode="signup" error={params.error} />;
}