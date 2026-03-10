"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

export default function ProtectedRoute({
  children,
  roleRequired,
}: {
  children: React.ReactNode;
  roleRequired?: string;
}) {
  const router = useRouter();
  const { user, loading } = useAuth();

  useEffect(() => {
    // Wait until the silent refresh has finished checking session
    if (loading) return;

    if (!user) {
      router.push("/login");
      return;
    }

    if (roleRequired && user.role !== roleRequired) {
      router.push("/dashboard");
    }
  }, [user, loading, router, roleRequired]);

  // Show nothing (or a loader) while verifying session
  if (loading) return null;

  return <>{children}</>;
}
