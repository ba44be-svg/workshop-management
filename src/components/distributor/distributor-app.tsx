"use client";

import * as React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Home, Package, Plus, ClipboardList, BarChart3, LogOut, Truck } from "lucide-react";
import { useDistributorAuthStore } from "@/store/distributor-auth-store";
import { DistributorDashboard } from "@/components/distributor/dashboard";
import { MyProducts } from "@/components/distributor/my-products";
import { NewSale } from "@/components/distributor/new-sale";
import { MySales } from "@/components/distributor/my-sales";
import { DistributorReports } from "@/components/distributor/reports";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

export type DistributorTab =
  | "home"
  | "products"
  | "new-sale"
  | "sales"
  | "reports";

interface TabDef {
  key: DistributorTab;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

const TABS: TabDef[] = [
  { key: "home", label: "خانه", icon: Home },
  { key: "products", label: "کالاهای من", icon: Package },
  { key: "new-sale", label: "فروش جدید", icon: Plus },
  { key: "sales", label: "فاکتورها", icon: ClipboardList },
  { key: "reports", label: "گزارش", icon: BarChart3 },
];

export function DistributorApp() {
  const { user, logout } = useDistributorAuthStore();
  const [tab, setTab] = React.useState<DistributorTab>("home");
  const [loggingOut, setLoggingOut] = React.useState(false);

  const handleLogout = async () => {
    setLoggingOut(true);
    await logout();
    setLoggingOut(false);
  };

  const goto = (t: DistributorTab) => setTab(t);

  return (
    <div
      dir="rtl"
      className="min-h-screen bg-gradient-to-b from-emerald-50/40 to-background text-foreground flex flex-col"
      style={{ maxWidth: "480px", margin: "0 auto" }}
    >
      {/* Top bar */}
      <header className="sticky top-0 z-30 flex items-center justify-between gap-2 border-b bg-white/95 backdrop-blur px-4 py-3 shadow-sm">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 text-white shadow">
            <Truck className="h-5 w-5" />
          </div>
          <div className="flex flex-col leading-tight">
            <span className="text-sm font-semibold">{user?.display_name ?? user?.first_name ?? "عامل پخش"}</span>
            <span className="text-[11px] text-muted-foreground">
              {user?.distributor_code ?? "D001"} · {user?.distributor_name ?? ""}
            </span>
          </div>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleLogout}
          disabled={loggingOut}
          className="text-muted-foreground hover:text-destructive"
        >
          <LogOut className="h-4 w-4 ml-1.5" />
          خروج
        </Button>
      </header>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto px-4 pb-24 pt-4">
        <AnimatePresence mode="wait">
          <motion.div
            key={tab}
            initial={{ opacity: 0, x: 12 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -12 }}
            transition={{ duration: 0.18 }}
          >
            {tab === "home" && <DistributorDashboard onGoto={goto} />}
            {tab === "products" && <MyProducts />}
            {tab === "new-sale" && <NewSale onDone={() => goto("sales")} />}
            {tab === "sales" && <MySales onNewSale={() => goto("new-sale")} />}
            {tab === "reports" && <DistributorReports />}
          </motion.div>
        </AnimatePresence>
      </main>

      {/* Bottom nav */}
      <nav className="fixed bottom-0 left-1/2 -translate-x-1/2 z-30 w-full max-w-[480px] border-t bg-white/95 backdrop-blur shadow-[0_-2px_10px_rgba(0,0,0,0.04)]">
        <div className="grid grid-cols-5 gap-1 px-1.5 py-1.5">
          {TABS.map((t) => {
            const Icon = t.icon;
            const active = tab === t.key;
            const isNewSale = t.key === "new-sale";
            return (
              <button
                key={t.key}
                onClick={() => goto(t.key)}
                className={cn(
                  "flex flex-col items-center justify-center gap-1 py-1.5 rounded-xl text-[11px] font-medium transition-all relative",
                  active
                    ? "text-emerald-700"
                    : "text-muted-foreground hover:text-emerald-700"
                )}
              >
                {isNewSale ? (
                  <div
                    className={cn(
                      "flex h-10 w-10 items-center justify-center rounded-2xl shadow-md transition-all -mt-3 mb-0.5",
                      "bg-gradient-to-br from-emerald-500 to-teal-600 text-white",
                      "ring-4 ring-emerald-50"
                    )}
                  >
                    <Icon className="h-5 w-5" />
                  </div>
                ) : (
                  <Icon
                    className={cn(
                      "h-5 w-5 transition-transform",
                      active && "scale-110"
                    )}
                  />
                )}
                <span className={cn(active && "font-semibold")}>{t.label}</span>
                {active && !isNewSale && (
                  <motion.span
                    layoutId="bottom-nav-dot"
                    className="absolute -bottom-0.5 h-1 w-8 rounded-full bg-emerald-500"
                  />
                )}
              </button>
            );
          })}
        </div>
      </nav>
    </div>
  );
}
