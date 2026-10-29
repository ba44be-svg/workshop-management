"use client";

import * as React from "react";
import { useAuthStore } from "@/store/auth-store";
import { LoginView } from "@/components/views/login-view";
import { AdminShell } from "@/components/layout/admin-shell";
import { Skeleton } from "@/components/ui/skeleton";

export default function Home() {
  const { status, hydrate } = useAuthStore();

  React.useEffect(() => {
    hydrate();
  }, [hydrate]);

  if (status === "loading") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3">
          <Skeleton className="h-12 w-12 rounded-full" />
          <Skeleton className="h-4 w-32" />
          <p className="text-xs text-muted-foreground">در حال بارگذاری…</p>
        </div>
      </div>
    );
  }

  if (status === "unauthenticated") {
    return <LoginView />;
  }

  return <AdminShell />;
}
