"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  ShoppingCart,
  PackageCheck,
  Truck,
  Factory,
  PackagePlus,
  ArrowLeft,
  Undo2,
  Clock,
  type LucideIcon,
} from "lucide-react";
import { api, type Paginated } from "@/lib/api";
import {
  MOCK_PURCHASES,
  MOCK_WORKSHOP_ISSUES,
  MOCK_WORKSHOP_RETURNS,
  MOCK_BATCHES,
  MOCK_PRODUCTION_OUTPUTS,
} from "@/lib/mock-data";
import { formatNumber, formatRial, formatDate, formatDateTime } from "@/lib/format";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useNavStore } from "@/store/nav-store";
import { PurchaseDialog } from "@/components/dialogs/purchase-dialog";
import { WorkshopIssueDialog } from "@/components/dialogs/workshop-issue-dialog";
import { WorkshopReturnDialog } from "@/components/dialogs/workshop-return-dialog";
import { ProductionBatchDialog } from "@/components/dialogs/production-batch-dialog";
import { ProductOutputDialog } from "@/components/dialogs/product-output-dialog";

type Purchase = (typeof MOCK_PURCHASES)[number];
type Issue = (typeof MOCK_WORKSHOP_ISSUES)[number];
type Return = (typeof MOCK_WORKSHOP_RETURNS)[number];
type Batch = (typeof MOCK_BATCHES)[number] & { product_name?: string; product_id?: number; };
type Output = (typeof MOCK_PRODUCTION_OUTPUTS)[number];

interface TimelineEvent {
  id: string;
  type: "purchase" | "issue" | "return" | "production_complete" | "output";
  label: string;
  ref: string;
  date: string;
  amount: string | number;
  qty: string | number;
  icon: LucideIcon;
}

const EVENT_META: Record<
  TimelineEvent["type"],
  { label: string; icon: LucideIcon; tone: string }
> = {
  purchase: { label: "خرید مواد اولیه", icon: ShoppingCart, tone: "bg-emerald-500/10 text-emerald-600" },
  issue: { label: "حواله به کارگاه", icon: Truck, tone: "bg-blue-500/10 text-blue-600" },
  return: { label: "برگشت از کارگاه", icon: Undo2, tone: "bg-amber-500/10 text-amber-600" },
  production_complete: { label: "تکمیل تولید", icon: Factory, tone: "bg-purple-500/10 text-purple-600" },
  output: { label: "خروج محصول", icon: PackagePlus, tone: "bg-rose-500/10 text-rose-600" },
};

// --- Status dot helpers -----------------------------------------------------
function statusDotColor(status: string): string {
  switch (status) {
    case "posted":
    case "completed":
      return "bg-emerald-500";
    case "draft":
    case "planned":
      return "bg-muted-foreground/30";
    case "in_progress":
      return "bg-blue-500";
    case "canceled":
    case "rejected":
      return "bg-rose-500";
    default:
      return "bg-muted-foreground/40";
  }
}

function StatusDots({ items }: { items: Array<{ status?: string }> }) {
  const slice = items.slice(0, 4);
  return (
    <div className="flex items-center gap-1" aria-label="وضعیت آخرین موارد">
      {Array.from({ length: 4 }).map((_, i) => {
        const item = slice[i];
        const color = item ? statusDotColor(item.status ?? "") : "bg-muted/30";
        return <span key={i} className={`inline-block h-2 w-2 rounded-full ${color}`} aria-hidden />;
      })}
    </div>
  );
}

// --- KPI cards --------------------------------------------------------------
function KpiCard({
  label,
  value,
  icon: Icon,
  tone,
  loading,
}: {
  label: string;
  value: number | string;
  icon: LucideIcon;
  tone: string;
  loading?: boolean;
}) {
  return (
    <Card>
      <CardContent className="flex items-center gap-3 p-4">
        <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${tone}`}>
          <Icon className="h-5 w-5" />
        </div>
        <div className="flex-1">
          <p className="text-xs text-muted-foreground">{label}</p>
          {loading ? (
            <Skeleton className="h-6 w-16" />
          ) : (
            <p className="text-lg font-bold nums">{value}</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function KpiRow() {
  const purchasesQ = useQuery({
    queryKey: ["purchases-today"],
    queryFn: () => api<Paginated<Purchase>>("/workshop/purchases/", { query: { page: 1, page_size: 50 } }),
  });
  const issuesQ = useQuery({
    queryKey: ["issues-active"],
    queryFn: () => api<Paginated<Issue>>("/workshop/issues/", { query: { page: 1, page_size: 50 } }),
  });
  const batchesQ = useQuery({
    queryKey: ["batches-in-progress"],
    queryFn: () => api<Paginated<Batch>>("/production/batches/", { query: { page: 1, page_size: 50, status: "in_progress" } }),
  });
  const outputsQ = useQuery({
    queryKey: ["outputs-today"],
    queryFn: () => api<Paginated<Output>>("/production/outputs/", { query: { page: 1, page_size: 50 } }).catch(() => null),
  });

  const today = new Date().toISOString().slice(0, 10);
  const purchasesToday = (purchasesQ.data?.results ?? []).filter((p) => p.purchase_date === today).length;
  const activeIssues = (issuesQ.data?.results ?? []).filter((i) => i.status !== "canceled").length;
  const inProgressBatches = batchesQ.data?.results.length ?? 0;
  const outputsToday = ((outputsQ.data as Paginated<Output> | null)?.results ?? MOCK_PRODUCTION_OUTPUTS).filter((o) => o.output_date === today).length;

  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
      <KpiCard label="خرید امروز" value={purchasesToday} icon={ShoppingCart} tone="bg-emerald-500/10 text-emerald-600" loading={purchasesQ.isLoading} />
      <KpiCard label="حواله فعال" value={activeIssues} icon={Truck} tone="bg-blue-500/10 text-blue-600" loading={issuesQ.isLoading} />
      <KpiCard label="تولید در حال" value={inProgressBatches} icon={Factory} tone="bg-purple-500/10 text-purple-600" loading={batchesQ.isLoading} />
      <KpiCard label="خروج امروز" value={outputsToday} icon={PackagePlus} tone="bg-rose-500/10 text-rose-600" loading={outputsQ.isLoading} />
      <KpiCard label="تحویل به عامل" value="—" icon={PackageCheck} tone="bg-amber-500/10 text-amber-600" />
    </div>
  );
}

// --- Stage cards (the cyclical dashboard) ------------------------------------
function StageCard({
  index,
  title,
  icon: Icon,
  tone,
  items,
  loading,
  refLabel,
  onAction,
  actionLabel,
}: {
  index: number;
  title: string;
  icon: LucideIcon;
  tone: string;
  items: Array<{ ref: string; subtitle?: string; status?: string; date?: string }>;
  loading?: boolean;
  refLabel: (item: { ref: string; subtitle?: string; status?: string; date?: string }) => React.ReactNode;
  onAction: () => void;
  actionLabel: string;
}) {
  return (
    <Card className="flex flex-col">
      <CardHeader className="flex-row items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <div className={`flex h-9 w-9 items-center justify-center rounded-lg ${tone}`}>
            <Icon className="h-5 w-5" />
          </div>
          <div>
            <CardTitle className="text-sm">{title}</CardTitle>
            <p className="text-[11px] text-muted-foreground">مرحله {index}</p>
          </div>
        </div>
        <Badge variant="outline" className="font-mono nums">#{index}</Badge>
      </CardHeader>
      <CardContent className="flex-1 space-y-3">
        <div className="flex items-center justify-between">
          <StatusDots items={items} />
          <span className="text-[11px] text-muted-foreground nums">{items.length} مورد اخیر</span>
        </div>
        <div className="space-y-1.5">
          {loading ? (
            <Skeleton className="h-16 w-full" />
          ) : items.length === 0 ? (
            <p className="text-xs text-muted-foreground py-3 text-center">موردی یافت نشد</p>
          ) : (
            items.slice(0, 5).map((item, i) => (
              <div key={i} className="flex items-center gap-2 rounded-md border p-2 text-xs">
                <span className={`h-2 w-2 rounded-full ${statusDotColor(item.status ?? "")}`} />
                <div className="flex-1 min-w-0">{refLabel(item)}</div>
                {item.date && <span className="text-muted-foreground whitespace-nowrap nums" dir="ltr">{formatDate(item.date)}</span>}
              </div>
            ))
          )}
        </div>
        <Button onClick={onAction} variant="outline" className="w-full">
          <Icon className="h-4 w-4" /> {actionLabel}
        </Button>
      </CardContent>
    </Card>
  );
}

function ProductionCycleSection({
  onPurchase,
  onIssue,
  onReturn,
  onBatch,
  onOutput,
}: {
  onPurchase: () => void;
  onIssue: () => void;
  onReturn: () => void;
  onBatch: () => void;
  onOutput: () => void;
}) {
  const purchasesQ = useQuery({
    queryKey: ["purchases-recent"],
    queryFn: () => api<Paginated<Purchase>>("/workshop/purchases/", { query: { page: 1, page_size: 5 } }),
  });
  const issuesQ = useQuery({
    queryKey: ["issues-recent"],
    queryFn: () => api<Paginated<Issue>>("/workshop/issues/", { query: { page: 1, page_size: 5 } }),
  });
  const batchesQ = useQuery({
    queryKey: ["batches-in-progress-list"],
    queryFn: () => api<Paginated<Batch>>("/production/batches/", { query: { page: 1, page_size: 5, status: "in_progress" } }),
  });
  const outputsQ = useQuery({
    queryKey: ["outputs-recent"],
    queryFn: () =>
      api<Paginated<Output>>("/production/outputs/", { query: { page: 1, page_size: 5 } }).catch(() => null),
  });

  const purchases = purchasesQ.data?.results ?? MOCK_PURCHASES;
  const issues = issuesQ.data?.results ?? MOCK_WORKSHOP_ISSUES;
  const batches = (batchesQ.data?.results ?? MOCK_BATCHES.filter((b) => b.status === "in_progress")) as Batch[];
  const outputs = (outputsQ.data as Paginated<Output> | null)?.results ?? MOCK_PRODUCTION_OUTPUTS;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">چرخه تولید</CardTitle>
        <CardDescription>۴ مرحله از خرید مواد تا خروج محصول</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
          <StageCard
            index={1}
            title="خرید مواد اولیه"
            icon={ShoppingCart}
            tone="bg-emerald-500/10 text-emerald-600"
            items={purchases.map((p) => ({ ref: p.purchase_no, subtitle: p.contractor_name, status: p.status, date: p.purchase_date }))}
            loading={purchasesQ.isLoading}
            refLabel={(it) => (
              <div className="flex flex-col">
                <span className="font-mono nums" dir="ltr">{it.ref}</span>
                {it.subtitle && <span className="text-muted-foreground">{it.subtitle}</span>}
              </div>
            )}
            onAction={onPurchase}
            actionLabel="خرید جدید"
          />
          <StageCard
            index={2}
            title="حواله به کارگاه"
            icon={Truck}
            tone="bg-blue-500/10 text-blue-600"
            items={issues.map((i) => ({ ref: i.issue_no, subtitle: i.contractor_name, status: i.status, date: i.issue_date }))}
            loading={issuesQ.isLoading}
            refLabel={(it) => (
              <div className="flex flex-col">
                <span className="font-mono nums" dir="ltr">{it.ref}</span>
                {it.subtitle && <span className="text-muted-foreground">{it.subtitle}</span>}
              </div>
            )}
            onAction={onIssue}
            actionLabel="حواله جدید"
          />
          <StageCard
            index={3}
            title="تولید در کارگاه"
            icon={Factory}
            tone="bg-purple-500/10 text-purple-600"
            items={batches.map((b) => ({ ref: b.batch_no, subtitle: b.product_name ?? b.product?.name, status: b.status, date: b.created_at }))}
            loading={batchesQ.isLoading}
            refLabel={(it) => (
              <div className="flex flex-col">
                <span className="font-mono nums" dir="ltr">{it.ref}</span>
                {it.subtitle && <span className="text-muted-foreground">{it.subtitle}</span>}
              </div>
            )}
            onAction={onBatch}
            actionLabel="ثبت تولید"
          />
          <StageCard
            index={4}
            title="خروج محصول"
            icon={PackagePlus}
            tone="bg-rose-500/10 text-rose-600"
            items={outputs.map((o) => ({ ref: o.output_no, subtitle: o.product_name, status: o.status, date: o.output_date }))}
            loading={outputsQ.isLoading}
            refLabel={(it) => (
              <div className="flex flex-col">
                <span className="font-mono nums" dir="ltr">{it.ref}</span>
                {it.subtitle && <span className="text-muted-foreground">{it.subtitle}</span>}
              </div>
            )}
            onAction={onOutput}
            actionLabel="خروج محصول"
          />
        </div>

        {/* Side links between stages */}
        <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-xs">
          <Button variant="link" size="sm" onClick={onReturn} className="text-amber-600">
            <Undo2 className="h-4 w-4" /> برگشت از کارگاه
          </Button>
          <DispatchLink />
        </div>
      </CardContent>
    </Card>
  );
}

function DispatchLink() {
  const { setView } = useNavStore();
  return (
    <Button variant="link" size="sm" onClick={() => setView("dispatch_transfers")} className="text-amber-600">
      تحویل به عامل پخش <ArrowLeft className="h-4 w-4" />
    </Button>
  );
}

// --- Timeline ----------------------------------------------------------------
function TimelineSection() {
  const purchasesQ = useQuery({
    queryKey: ["timeline-purchases"],
    queryFn: () => api<Paginated<Purchase>>("/workshop/purchases/", { query: { page: 1, page_size: 20 } }),
  });
  const issuesQ = useQuery({
    queryKey: ["timeline-issues"],
    queryFn: () => api<Paginated<Issue>>("/workshop/issues/", { query: { page: 1, page_size: 20 } }),
  });
  const returnsQ = useQuery({
    queryKey: ["timeline-returns"],
    queryFn: () => api<Paginated<Return>>("/workshop/returns/", { query: { page: 1, page_size: 20 } }),
  });
  const batchesQ = useQuery({
    queryKey: ["timeline-batches"],
    queryFn: () => api<Paginated<Batch>>("/production/batches/", { query: { page: 1, page_size: 20 } }),
  });
  const outputsQ = useQuery({
    queryKey: ["timeline-outputs"],
    queryFn: () =>
      api<Paginated<Output>>("/production/outputs/", { query: { page: 1, page_size: 20 } }).catch(() => null),
  });

  const events: TimelineEvent[] = React.useMemo(() => {
    const list: TimelineEvent[] = [];
    (purchasesQ.data?.results ?? []).forEach((p) => {
      list.push({
        id: `pur-${p.id}`,
        type: "purchase",
        label: `خرید از ${p.contractor_name}`,
        ref: p.purchase_no,
        date: p.purchase_date,
        amount: p.total_amount,
        qty: p.total_qty,
        icon: EVENT_META.purchase.icon,
      });
    });
    (issuesQ.data?.results ?? []).forEach((i) => {
      list.push({
        id: `iss-${i.id}`,
        type: "issue",
        label: `حواله به ${i.contractor_name}`,
        ref: i.issue_no,
        date: i.issue_date,
        amount: i.total_value,
        qty: i.total_qty,
        icon: EVENT_META.issue.icon,
      });
    });
    (returnsQ.data?.results ?? []).forEach((r) => {
      list.push({
        id: `ret-${r.id}`,
        type: "return",
        label: `برگشت از ${r.contractor_name}`,
        ref: r.return_no,
        date: r.return_date,
        amount: r.total_value,
        qty: r.total_qty,
        icon: EVENT_META.return.icon,
      });
    });
    (batchesQ.data?.results ?? []).filter((b) => b.status === "completed").forEach((b) => {
      list.push({
        id: `bat-${b.id}`,
        type: "production_complete",
        label: `تکمیل بچ ${b.product_name ?? b.product?.name ?? ""}`,
        ref: b.batch_no,
        date: b.completed_at ?? b.created_at,
        amount: 0,
        qty: b.actual_qty,
        icon: EVENT_META.production_complete.icon,
      });
    });
    ((outputsQ.data as Paginated<Output> | null)?.results ?? []).forEach((o) => {
      list.push({
        id: `out-${o.id}`,
        type: "output",
        label: `خروج محصول ${o.product_name}`,
        ref: o.output_no,
        date: o.output_date,
        amount: o.total_value,
        qty: o.total_qty,
        icon: EVENT_META.output.icon,
      });
    });
    list.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
    return list.slice(0, 30);
  }, [purchasesQ.data, issuesQ.data, returnsQ.data, batchesQ.data, outputsQ.data]);

  const loading =
    purchasesQ.isLoading || issuesQ.isLoading || returnsQ.isLoading || batchesQ.isLoading || outputsQ.isLoading;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">تایم‌لاین رویدادها</CardTitle>
        <CardDescription>آخرین رویدادها در ۴ مرحله تولید</CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-2">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        ) : events.length === 0 ? (
          <p className="text-sm text-muted-foreground py-6 text-center">رویدادی برای نمایش وجود ندارد.</p>
        ) : (
          <div className="space-y-1.5">
            {events.map((e) => {
              const meta = EVENT_META[e.type];
              const Icon = e.icon;
              return (
                <div key={e.id} className="flex items-center gap-3 rounded-md border p-2.5 text-sm">
                  <div className={`flex h-8 w-8 items-center justify-center rounded-md ${meta.tone}`}>
                    <Icon className="h-4 w-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{meta.label}</p>
                    <p className="text-xs text-muted-foreground truncate">{e.label}</p>
                  </div>
                  <div className="flex flex-col items-end text-xs">
                    <span className="font-mono nums" dir="ltr">{e.ref}</span>
                    <span className="text-muted-foreground nums" dir="ltr">{formatDate(e.date)}</span>
                  </div>
                  <div className="flex flex-col items-end text-xs whitespace-nowrap">
                    {Number(e.amount) > 0 && <span className="nums">{formatRial(e.amount)}</span>}
                    {Number(e.qty) > 0 && <span className="text-muted-foreground nums">{formatNumber(e.qty)} عدد</span>}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// --- Main view --------------------------------------------------------------
export function ProductionView() {
  const [purchaseOpen, setPurchaseOpen] = React.useState(false);
  const [issueOpen, setIssueOpen] = React.useState(false);
  const [returnOpen, setReturnOpen] = React.useState(false);
  const [batchOpen, setBatchOpen] = React.useState(false);
  const [outputOpen, setOutputOpen] = React.useState(false);

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>داشبورد تولید</CardTitle>
          <CardDescription>نمای کلی چرخه تولید: خرید، حواله، تولید، خروج</CardDescription>
        </CardHeader>
      </Card>

      {/* Section 1 — Summary cards */}
      <KpiRow />

      {/* Section 2 — Production cycle */}
      <ProductionCycleSection
        onPurchase={() => setPurchaseOpen(true)}
        onIssue={() => setIssueOpen(true)}
        onReturn={() => setReturnOpen(true)}
        onBatch={() => setBatchOpen(true)}
        onOutput={() => setOutputOpen(true)}
      />

      {/* Section 3 — Timeline */}
      <TimelineSection />

      {/* Wizard dialogs */}
      <PurchaseDialog open={purchaseOpen} onOpenChange={setPurchaseOpen} />
      <WorkshopIssueDialog open={issueOpen} onOpenChange={setIssueOpen} />
      <WorkshopReturnDialog open={returnOpen} onOpenChange={setReturnOpen} />
      <ProductionBatchDialog open={batchOpen} onOpenChange={setBatchOpen} />
      <ProductOutputDialog open={outputOpen} onOpenChange={setOutputOpen} />
    </div>
  );
}
