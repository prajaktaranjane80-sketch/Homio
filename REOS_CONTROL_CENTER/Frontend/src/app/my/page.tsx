import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import {
  SESSION_COOKIE,
  readSessionCookie,
} from "@/lib/auth/oidc";

import MyHomioShell from "@/features/f07_my_homio/MyHomioShell";

import type { MyHomioProfile } from "@/features/f07_my_homio/my-homio.types";

export const metadata = {
  title: "My HOMIO",
  robots: { index: false, follow: false },
};

export const dynamic = "force-dynamic";

export default async function MyHomioAccountPage() {
  const cookieStore = await cookies();

  const session = readSessionCookie(
    cookieStore.get(SESSION_COOKIE)?.value,
  );

  if (!session) {
    redirect("/login?returnTo=%2Fmy");
  }

  const profile: MyHomioProfile = {
    name: session.name,
    email: session.email,
    emailVerified: session.emailVerified,
  };

  return <MyHomioShell profile={profile} />;
}
