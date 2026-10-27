"use client";

import * as React from "react";
import {
  LayoutDashboard,
  Package,
  Factory,
  ShoppingCart,
  Send,
  PackageCheck,
  Boxes,
  Warehouse,
  BookOpen,
  Truck,
  Moon,
  Sun,
  LogOut,
  Menu,
  BarChart3,
  Settings,
} from "lucide-react";
import { useTheme } from "next-themes";
import { motion, AnimatePresence } from "framer-motion";
import { useAuthStore } from "@/store/auth-store";
import { useNavStore, type ViewKey } from "@/store/nav-store";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import {
  Sheet,
  SheetContent,
  SheetTrigger,
} from "@/components/ui/sheet";
import { cn } from "@/lib/utils";
import { isDemoMode, subscribeDemoMode } from "@/lib/api";
import { useConfig, ICON_MAP } from "@/store/config-store";
import { THEMES } from "@/lib/themes";

import { DashboardView } from "@/components/views/dashboard-view";
import { ProductsView } from "@/components/views/products-view";
import { PurchaseView } from "@/components/views/purchase-view";
import { WorkshopIssueView } from "@/components/views/workshop-issue-view";
import { ProductionView } from "@/components/views/production-view";
import { ProductOutputView } from "@/components/views/product-output-view";
import { FinishedGoodsView } from "@/components/views/finished-goods-view";
import { SalesView } from "@/components/views/sales-view";
import { InventoryView } from "@/components/views/inventory-view";
import { AccountingView } from "@/components/views/accounting-view";
import { DispatchTransfersView } from "@/components/views/dispatch-transfers-view";
import { ReportsView } from "@/components/views/reports-view";
import { SettingsView } from "@/components/views/settings-view";

interface NavItem {
  key: ViewKey;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
}

const NAV: NavItem[] = [
  { key: "dashboard", label: "داشبورد", icon: LayoutDashboard, description: "نمای کلی" },
  { key: "products", label: "محصولات", icon: Package, description: "مدیریت کالاها" },
  { key: "purchase", label: "خرید مواد اولیه", icon: ShoppingCart, description: "خرید از کارپرداز" },
  { key: "workshop_issue", label: "حواله به کارگاه", icon: Send, description: "حواله مواد اولیه" },
  { key: "production", label: "تولید در کارگاه", icon: Factory, description: "بچ‌های تولید" },
  { key: "product_output", label: "خروج از کارگاه", icon: PackageCheck, description: "خروج محصول" },
  { key: "finished_goods", label: "انبار محصول", icon: Boxes, description: "موجودی محصولات" },
  { key: "sales", label: "فروش", icon: ShoppingCart, description: "فاکتورهای فروش" },
  { key: "inventory", label: "انبار (FEFO)", icon: Warehouse, description: "موجودی و لات‌ها" },
  { key: "accounting", label: "حسابداری", icon: BookOpen, description: "اسناد حسابداری" },
  { key: "dispatch_transfers", label: "پخش و انتقال", icon: Truck, description: "سندهای پخش" },
  { key: "reports", label: "گزارش‌ها", icon: BarChart3, description: "گزارش‌های تفصیلی" },
  { key: "settings", label: "تنظیمات", icon: Settings, description: "پیکربندی سیستم" },
];

function NavList({ onNavigate }: { onNavigate?: () => void }) {
  const { view, setView } = useNavStore();
  return (
    <nav className="flex flex-col gap-1" aria-label="ناوبری اصلی">
      {NAV.map((item) => {
        const Icon = item.icon;
        const active = view === item.key;
        return (
          <button
            key={item.key}
            onClick={() => {
              setView(item.key);
              onNavigate?.();
            }}
            className={cn(
              "group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors w-full text-right",
              active
                ? "bg-sidebar-accent text-sidebar-accent-foreground"
                : "text-sidebar-foreground/70 hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground"
            )}
            aria-current={active ? "page" : undefined}
          >
            <Icon
              className={cn(
                "h-5 w-5 shrink-0 transition-colors",
                active ? "text-primary" : "text-muted-foreground group-hover:text-primary"
              )}
            />
            <span className="flex-1 truncate">{item.label}</span>
            {active && <span className="h-1.5 w-1.5 rounded-full bg-primary" />}
          </button>
        );
      })}
    </nav>
  );
}

function NavListHorizontal({ onNavigate }: { onNavigate?: () => void }) {
  const { view, setView } = useNavStore();
  return (
    <nav className="flex flex-row items-center gap-1 overflow-x-auto scroll-pretty" aria-label="ناوبری بالا">
      {NAV.map((item) => {
        const Icon = item.icon;
        const active = view === item.key;
        return (
          <button
            key={item.key}
            onClick={() => {
              setView(item.key);
              onNavigate?.();
            }}
            className={cn(
              "group flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium transition-colors whitespace-nowrap",
              active
                ? "bg-sidebar-accent text-sidebar-accent-foreground"
                : "text-sidebar-foreground/70 hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground"
            )}
            aria-current={active ? "page" : undefined}
          >
            <Icon className={cn("h-4 w-4 shrink-0", active ? "text-primary" : "text-muted-foreground")} />
            <span className="truncate">{item.label}</span>
          </button>
        );
      })}
    </nav>
  );
}

function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = React.useState(false);
  React.useEffect(() => setMounted(true), []);
  if (!mounted) return <div className="h-9 w-9" />;
  const isDark = theme === "dark";
  return (
    <Button
      variant="ghost"
      size="icon"
      aria-label="تغییر تم"
      onClick={() => setTheme(isDark ? "light" : "dark")}
    >
      {isDark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
    </Button>
  );
}

function UserMenu() {
  const { user, logout } = useAuthStore();
  const initials = user
    ? `${user.first_name?.[0] ?? ""}${user.last_name?.[0] ?? ""}`
    : "؟";
  return (
    <div className="flex items-center gap-2">
      <Avatar className="h-9 w-9">
        <AvatarFallback className="bg-primary text-primary-foreground text-xs font-semibold">
          {initials || "مک"}
        </AvatarFallback>
      </Avatar>
      <div className="hidden sm:flex flex-col items-end leading-tight">
        <span className="text-sm font-medium">{user?.display_name ?? user?.username ?? "کاربر"}</span>
        <Badge variant="secondary" className="text-[10px] py-0 px-1.5">
          {user?.role ?? "—"}
        </Badge>
      </div>
      <Button
        variant="ghost"
        size="icon"
        aria-label="خروج"
        onClick={() => logout()}
      >
        <LogOut className="h-5 w-5" />
      </Button>
    </div>
  );
}

function SidebarContent({ onNavigate, horizontal = false }: { onNavigate?: () => void; horizontal?: boolean }) {
  const { title, iconKey } = useConfig();
  const Icon = ICON_MAP[iconKey] ?? Factory;
  if (horizontal) {
    return (
      <div className="flex h-full w-full flex-col">
        <div className="flex items-center gap-3 border-b border-sidebar-border px-4 py-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Icon className="h-4 w-4" />
          </div>
          <div className="flex flex-col leading-tight">
            <span className="text-sm font-semibold">{title}</span>
          </div>
          <div className="flex-1" />
          <NavListHorizontal onNavigate={onNavigate} />
        </div>
      </div>
    );
  }
  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2 px-4 py-5 border-b border-sidebar-border">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <Icon className="h-5 w-5" />
        </div>
        <div className="flex flex-col leading-tight">
          <span className="text-sm font-semibold">{title}</span>
          <span className="text-[11px] text-muted-foreground">مدیریت یکپارچه</span>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto scroll-pretty px-3 py-4">
        <NavList onNavigate={onNavigate} />
      </div>
      <div className="border-t border-sidebar-border px-4 py-3 text-[11px] text-muted-foreground">
        نسخه ۱.۰ • ساخته‌شده با Next.js
      </div>
    </div>
  );
}

function MobileSidebar() {
  const [open, setOpen] = React.useState(false);
  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="ghost" size="icon" aria-label="باز کردن منو" className="md:hidden">
          <Menu className="h-5 w-5" />
        </Button>
      </SheetTrigger>
      <SheetContent side="right" className="w-72 p-0">
        <SidebarContent onNavigate={() => setOpen(false)} />
      </SheetContent>
    </Sheet>
  );
}

function ViewRenderer() {
  const { view } = useNavStore();
  const current = (
    <>
      {view === "dashboard" && <DashboardView />}
      {view === "products" && <ProductsView />}
      {view === "purchase" && <PurchaseView />}
      {view === "workshop_issue" && <WorkshopIssueView />}
      {view === "production" && <ProductionView />}
      {view === "product_output" && <ProductOutputView />}
      {view === "finished_goods" && <FinishedGoodsView />}
      {view === "sales" && <SalesView />}
      {view === "inventory" && <InventoryView />}
      {view === "accounting" && <AccountingView />}
      {view === "dispatch_transfers" && <DispatchTransfersView />}
      {view === "reports" && <ReportsView />}
      {view === "settings" && <SettingsView />}
    </>
  );
  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={view}
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -8 }}
        transition={{ duration: 0.18 }}
      >
        {current}
      </motion.div>
    </AnimatePresence>
  );
}

// نشانگر بصری "حالت دمو" — وقتی بک‌اند در دسترس نیست و React دارد از داده‌های mock استفاده می‌کند
function DemoModeBanner() {
  const [demo, setDemo] = React.useState(isDemoMode());
  React.useEffect(() => {
    const unsub = subscribeDemoMode(setDemo);
    return unsub;
  }, []);
  if (!demo) return null;
  return (
    <div
      role="status"
      className="sticky top-0 z-40 flex items-center justify-center gap-2 bg-amber-500 text-amber-950 px-4 py-1.5 text-xs font-medium shadow-md"
      dir="rtl"
    >
      <span aria-hidden>⚠️</span>
      <span>
        حالت دمو فعال — بک‌اند (Django روی پورت ۸۰۰۰) در دسترس نیست.
        داده‌ها از حافظه موقت خوانده می‌شوند و با رفرش صفحه از بین می‌روند.
      </span>
    </div>
  );
}

// Apply theme + brand-color + layout to the document element on mount and whenever they change.
function useApplyConfigEffects() {
  const { theme, brandColor } = useConfig();
  React.useEffect(() => {
    if (typeof document === "undefined") return;
    const root = document.documentElement;
    root.setAttribute("data-theme", theme);
    root.style.setProperty("--brand-color", brandColor);
    // Apply card style class globally so Card components can pick it up if they opt in.
    root.classList.remove("card-style-glass", "card-style-flat", "card-style-subtle-gradient");
    root.classList.add(`card-style-${THEMES[theme]?.cardStyle ?? "flat"}`);
  }, [theme, brandColor]);
}

export function AdminShell() {
  const { view } = useNavStore();
  const { title, layout } = useConfig();
  const active = NAV.find((n) => n.key === view);
  useApplyConfigEffects();

  const isTopbar = layout === "topbar";
  const isSidebarLeft = layout === "sidebar-left";

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <DemoModeBanner />
      {isTopbar ? (
        <div className="flex flex-1 flex-col">
          {/* Top navigation bar */}
          <header className="sticky top-0 z-40 border-b bg-sidebar">
            <SidebarContent horizontal />
          </header>
          <header className="sticky top-[var(--topbar-offset,0px)] z-30 flex h-16 items-center justify-between gap-3 border-b bg-background/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/70">
            <div className="flex items-center gap-3">
              <MobileSidebar />
              <div className="flex flex-col leading-tight">
                <h1 className="text-base font-semibold">{active?.label ?? "داشبورد"}</h1>
                <p className="hidden sm:block text-[11px] text-muted-foreground">
                  {active?.description}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <ThemeToggle />
              <UserMenu />
            </div>
          </header>
          <main className="flex-1 p-4 sm:p-6">
            <ViewRenderer />
          </main>
          <footer className="mt-auto border-t bg-background px-4 py-4 text-center text-xs text-muted-foreground">
            © {new Date().getFullYear()} {title} — تمامی حقوق محفوظ است.
          </footer>
        </div>
      ) : (
        <div className={cn("flex flex-1 flex-col md:flex-row", isSidebarLeft && "md:flex-row-reverse")}>
          {/* Desktop sidebar */}
          <aside className="hidden md:flex md:w-64 md:shrink-0 border-l border-sidebar-border bg-sidebar">
            <div className="w-full">
              <SidebarContent />
            </div>
          </aside>

          {/* Main column */}
          <div className="flex min-w-0 flex-1 flex-col">
            <header className="sticky top-0 z-30 flex h-16 items-center justify-between gap-3 border-b bg-background/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/70">
              <div className="flex items-center gap-3">
                <MobileSidebar />
                <div className="flex flex-col leading-tight">
                  <h1 className="text-base font-semibold">{active?.label ?? "داشبورد"}</h1>
                  <p className="hidden sm:block text-[11px] text-muted-foreground">
                    {active?.description}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-1">
                <ThemeToggle />
                <UserMenu />
              </div>
            </header>

            <main className="flex-1 p-4 sm:p-6">
              <ViewRenderer />
            </main>

            <footer className="mt-auto border-t bg-background px-4 py-4 text-center text-xs text-muted-foreground">
              © {new Date().getFullYear()} {title} — تمامی حقوق محفوظ است.
            </footer>
          </div>
        </div>
      )}
    </div>
  );
}
