"use client";

import * as React from "react";
import { useDistributorAuthStore } from "@/store/distributor-auth-store";
import { DistributorLogin } from "@/components/distributor/login";
import { DistributorApp } from "@/components/distributor/distributor-app";
import { Skeleton } from "@/components/ui/skeleton";

export default function DistributorPage() {
  const { status, hydrate } = useDistributorAuthStore();

  React.useEffect(() => {
    hydrate();
  }, [hydrate]);

  if (status === "loading") {
    return (
      <div
        dir="rtl"
        className="flex min-h-screen items-center justify-center bg-gradient-to-b from-emerald-50 to-background"
      >
        <div className="flex flex-col items-center gap-3">
          <Skeleton className="h-14 w-14 rounded-2xl" />
          <Skeleton className="h-4 w-40" />
          <p className="text-xs text-muted-foreground">در حال بارگذاری…</p>
        </div>
      </div>
    );
  }

  if (status === "unauthenticated") {
    return <DistributorLogin />;
  }

  return <DistributorApp />;
}
