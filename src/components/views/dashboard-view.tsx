"use client";

import * as React from "react";
import {
  Factory,
  ShoppingCart,
  Truck,
  AlertTriangle,
  ArrowLeft,
  type LucideIcon,
} from "lucide-react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  Cell,
  Pie,
  PieChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { api, type Paginated } from "@/lib/api";
import {
  batchStatusBreakdown,
  dashboardKpis,
  productionLast7Days,
  recentActivities,
  salesLast7Days,
  MOCK_BATCHES,
} from "@/lib/mock-data";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { formatRial, relativeTime } from "@/lib/format";

interface Kpi {
  icon: LucideIcon;
  label: string;
  queryKey: string;
  loading: boolean;
  value: string;
  hint: string;
  tone: "primary" | "chart2" | "chart3" | "destructive";
}

function useDashboardData() {
  const kpis = useQuery({
    queryKey: ["dashboard-kpis"],
    queryFn: () => dashboardKpis(),
  });
  const sales = useQuery({
    queryKey: ["dashboard-sales7"],
    queryFn: () => salesLast7Days(),
  });
  const production = useQuery({
    queryKey: ["dashboard-prod7"],
    queryFn: () => productionLast7Days(),
  });
  const batchStatus = useQuery({
    queryKey: ["dashboard-batch-status"],
    queryFn: () => batchStatusBreakdown(),
  });
  const batches = useQuery({
    queryKey: ["dashboard-recent-batches"],
    queryFn: () =>
      api<Paginated<(typeof MOCK_BATCHES)[number] & { product_name?: string; product_id?: number }>>("/production/batches/", {
        query: { page: 1, page_size: 5 },
      }),
  });
  return { kpis, sales, production, batchStatus, batches };
}

// D01-1: هوک برای رفرش خودکار داشبورد بعد از تغییرات
export function useDashboardRefresh() {
  const qc = useQueryClient();
  return React.useCallback(() => {
    qc.invalidateQueries({ queryKey: ["dashboard-kpis"] });
    qc.invalidateQueries({ queryKey: ["dashboard-sales7"] });
    qc.invalidateQueries({ queryKey: ["dashboard-prod7"] });
    qc.invalidateQueries({ queryKey: ["dashboard-batch-status"] });
    qc.invalidateQueries({ queryKey: ["dashboard-recent-batches"] });
  }, [qc]);
}

const STATUS_COLORS: Record<string, string> = {
  planned: "var(--chart-4)",
  in_progress: "var(--chart-1)",
  completed: "var(--chart-3)",
  canceled: "var(--chart-5)",
};

const STATUS_LABEL: Record<string, string> = {
  planned: "برنامه‌ریزی‌شده",
  in_progress: "در حال اجرا",
  completed: "تکمیل‌شده",
  canceled: "لغوشده",
};

const ACTIVITY_ICON: Record<string, LucideIcon> = {
  sale: ShoppingCart,
  batch: Factory,
  dispatch: Truck,
  lot: AlertTriangle,
  journal: ArrowLeft,
};

export function DashboardView() {
  const { kpis, sales, production, batchStatus, batches } = useDashboardData();
  const loading = kpis.isLoading;
  const k = kpis.data;

  const cards: Kpi[] = [
    {
      icon: Factory,
      label: "بچ‌های تولید امروز",
      queryKey: "batches_today",
      loading,
      value: k ? String(k.batches_today) : "—",
      hint: "ساخته‌شده در جریان روز",
      tone: "primary",
    },
    {
      icon: ShoppingCart,
      label: "فروش امروز (ریال)",
      queryKey: "sales_today",
      loading,
      value: k ? formatRial(k.sales_today_rial) : "—",
      hint: "مجموع فروش ثبت‌شده امروز",
      tone: "chart2",
    },
    {
      icon: Truck,
      label: "سندهای پخش فعال",
      queryKey: "active_dispatches",
      loading,
      value: k ? String(k.active_dispatches) : "—",
      hint: "در حال بارگذاری یا حمل",
      tone: "chart3",
    },
    {
      icon: AlertTriangle,
      label: "لات‌های نزدیک انقضا",
      queryKey: "near_expiry",
      loading,
      value: k ? String(k.near_expiry_lots) : "—",
      hint: "≤ ۷ روز تا انقضا",
      tone: "destructive",
    },
  ];

  const toneBg: Record<Kpi["tone"], string> = {
    primary: "bg-primary/10 text-primary",
    chart2: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
    chart3: "bg-amber-500/10 text-amber-600 dark:text-amber-400",
    destructive: "bg-rose-500/10 text-rose-600 dark:text-rose-400",
  };

  return (
    <div className="space-y-6">
      {/* KPI cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {cards.map((c, i) => {
          const Icon = c.icon;
          return (
            <motion.div
              key={c.queryKey}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.25, delay: i * 0.05 }}
            >
              <Card className="overflow-hidden">
                <CardContent className="flex items-center gap-4 p-5">
                  <div className={`flex h-12 w-12 items-center justify-center rounded-xl ${toneBg[c.tone]}`}>
                    <Icon className="h-6 w-6" />
                  </div>
                  <div className="flex-1 space-y-1">
                    <p className="text-xs text-muted-foreground">{c.label}</p>
                    {c.loading ? (
                      <Skeleton className="h-7 w-24" />
                    ) : (
                      <p className="text-xl font-bold tracking-tight nums">{c.value}</p>
                    )}
                    <p className="text-[11px] text-muted-foreground">{c.hint}</p>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">روند فروش ۷ روز اخیر</CardTitle>
            <CardDescription>مجموع فروش روزانه به ریال</CardDescription>
          </CardHeader>
          <CardContent>
            {sales.isLoading ? (
              <Skeleton className="h-64 w-full" />
            ) : (
              <div className="h-64 w-full" dir="ltr">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={sales.data}>
                    <defs>
                      <linearGradient id="salesGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="var(--chart-1)" stopOpacity={0.45} />
                        <stop offset="100%" stopColor="var(--chart-1)" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                    <XAxis dataKey="date" tick={{ fontSize: 11 }} stroke="var(--muted-foreground)" />
                    <YAxis
                      tickFormatter={(v) => `${Math.round(v / 1000000)}م`}
                      tick={{ fontSize: 11 }}
                      stroke="var(--muted-foreground)"
                    />
                    <Tooltip
                      formatter={(v: number) => [formatRial(v), "فروش"]}
                      contentStyle={{
                        background: "var(--popover)",
                        border: "1px solid var(--border)",
                        borderRadius: 8,
                        fontSize: 12,
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="فروش"
                      stroke="var(--chart-1)"
                      strokeWidth={2}
                      fill="url(#salesGrad)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">تولید روزانه و ضایعات</CardTitle>
            <CardDescription>مقادیر تولید و ضایعات ۷ روز اخیر</CardDescription>
          </CardHeader>
          <CardContent>
            {production.isLoading ? (
              <Skeleton className="h-64 w-full" />
            ) : (
              <div className="h-64 w-full" dir="ltr">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={production.data}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                    <XAxis dataKey="date" tick={{ fontSize: 11 }} stroke="var(--muted-foreground)" />
                    <YAxis tick={{ fontSize: 11 }} stroke="var(--muted-foreground)" />
                    <Tooltip
                      contentStyle={{
                        background: "var(--popover)",
                        border: "1px solid var(--border)",
                        borderRadius: 8,
                        fontSize: 12,
                      }}
                    />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                    <Bar dataKey="تولید" fill="var(--chart-3)" radius={[6, 6, 0, 0]} />
                    <Bar dataKey="ضایعات" fill="var(--chart-5)" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-base">وضعیت بچ‌های تولید</CardTitle>
            <CardDescription>تفکیک بر اساس وضعیت</CardDescription>
          </CardHeader>
          <CardContent>
            {batchStatus.isLoading ? (
              <Skeleton className="h-64 w-full" />
            ) : (
              <div className="h-64 w-full" dir="ltr">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={batchStatus.data}
                      dataKey="value"
                      nameKey="name"
                      innerRadius={50}
                      outerRadius={85}
                      paddingAngle={2}
                    >
                      {batchStatus.data?.map((entry) => (
                        <Cell key={entry.key} fill={STATUS_COLORS[entry.key]} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        background: "var(--popover)",
                        border: "1px solid var(--border)",
                        borderRadius: 8,
                        fontSize: 12,
                      }}
                    />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">آخرین فعالیت‌ها</CardTitle>
            <CardDescription>۵ رویداد اخیر سامانه</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {recentActivities().map((a) => {
                const Icon = ACTIVITY_ICON[a.type] ?? ArrowLeft;
                return (
                  <div key={a.id} className="flex items-center gap-3 rounded-lg border bg-card/50 p-3">
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-accent text-accent-foreground">
                      <Icon className="h-4 w-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{a.title}</p>
                      <p className="text-xs text-muted-foreground truncate">{a.subtitle}</p>
                    </div>
                    <span className="text-[11px] text-muted-foreground whitespace-nowrap">
                      {relativeTime(a.at)}
                    </span>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent batches table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">آخرین بچ‌های تولید</CardTitle>
          <CardDescription>۵ بچ اخیر همراه با وضعیت</CardDescription>
        </CardHeader>
        <CardContent>
          {batches.isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          ) : (
            <div className="overflow-x-auto scroll-pretty">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-right text-muted-foreground border-b">
                    <th className="px-3 py-2 font-medium">شماره بچ</th>
                    <th className="px-3 py-2 font-medium">محصول</th>
                    <th className="px-3 py-2 font-medium">برنامه</th>
                    <th className="px-3 py-2 font-medium">تولید واقعی</th>
                    <th className="px-3 py-2 font-medium">وضعیت</th>
                  </tr>
                </thead>
                <tbody>
                  {batches.data?.results.map((b) => (
                    <tr key={b.id} className="border-b last:border-0 hover:bg-muted/40">
                      <td className="px-3 py-2 font-mono nums">{b.batch_no}</td>
                      <td className="px-3 py-2">{b.product_name ?? b.product?.name ?? "—"}</td>
                      <td className="px-3 py-2 nums">{b.planned_qty}</td>
                      <td className="px-3 py-2 nums">{b.actual_qty}</td>
                      <td className="px-3 py-2">
                        <Badge
                          variant="outline"
                          style={{ color: STATUS_COLORS[b.status], borderColor: STATUS_COLORS[b.status] }}
                        >
                          {STATUS_LABEL[b.status] ?? b.status}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
