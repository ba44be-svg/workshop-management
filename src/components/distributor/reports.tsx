"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  BarChart3,
  TrendingUp,
  Wallet,
  Package,
  ShoppingBag,
  Hash,
  Calendar,
  Truck,
} from "lucide-react";
import { api } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { formatRial, formatNumber, formatDate } from "@/lib/format";
import { cn } from "@/lib/utils";

type ReportTab = "sales" | "commission" | "balance";

interface MySalesReport {
  period_days: number;
  total_sales: string;
  total_count: number;
  avg_sale: string;
  consignment_count: number;
  firm_count: number;
  results: Array<{
    sale_id: number;
    sale_no: string;
    sale_date: string;
    store_name: string;
    total_amount: string;
    sales_type: string;
    sales_type_display: string;
    status: string;
    status_display: string;
  }>;
}

interface MyCommissionReport {
  period_days: number;
  distributor_id: number;
  distributor_name: string;
  distributor_code: string;
  commission_rate: string;
  total_sales: string;
  commission_owed: string;
  commission_paid: string;
  balance: string;
}

interface MyProductBalanceReport {
  distributor_id: number;
  distributor_name: string;
  total_qty: string;
  total_value: string;
  results: Array<{
    product_id: number;
    product_name: string;
    product_code: string;
    qty: string;
    unit_price: string;
    total_value: string;
    dispatch_no: string;
    dispatch_date: string;
  }>;
}

export function DistributorReports() {
  const [tab, setTab] = React.useState<ReportTab>("sales");

  return (
    <div className="space-y-3">
      <div>
        <h2 className="text-lg font-bold">گزارش‌ها</h2>
        <p className="text-xs text-muted-foreground">
          گزارش فروش، پورسانت و مانده کالای خود.
        </p>
      </div>

      {/* Tab switcher */}
      <div className="grid grid-cols-3 gap-1 rounded-xl bg-muted p-1">
        <TabBtn active={tab === "sales"} onClick={() => setTab("sales")} icon={<ShoppingBag className="h-4 w-4" />}>
          فروش من
        </TabBtn>
        <TabBtn active={tab === "commission"} onClick={() => setTab("commission")} icon={<TrendingUp className="h-4 w-4" />}>
          پورسانت
        </TabBtn>
        <TabBtn active={tab === "balance"} onClick={() => setTab("balance")} icon={<Package className="h-4 w-4" />}>
          مانده کالا
        </TabBtn>
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={tab}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.18 }}
        >
          {tab === "sales" && <SalesReport />}
          {tab === "commission" && <CommissionReport />}
          {tab === "balance" && <BalanceReport />}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}

function TabBtn({
  active,
  onClick,
  icon,
  children,
}: {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "flex items-center justify-center gap-1.5 rounded-lg py-2 text-xs font-medium transition-all",
        active
          ? "bg-white shadow text-emerald-700"
          : "text-muted-foreground hover:text-foreground"
      )}
    >
      {icon}
      {children}
    </button>
  );
}

function SalesReport() {
  const { data, isLoading } = useQuery({
    queryKey: ["distributor", "report", "my_sales"],
    queryFn: () => api<MySalesReport>("/reports/my_sales/"),
  });

  if (isLoading) return <ReportSkeleton />;

  const d = data;
  return (
    <div className="space-y-3">
      {/* Big KPI */}
      <Card className="border-emerald-200 bg-gradient-to-l from-emerald-600 to-teal-600 text-white">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs opacity-90 flex items-center gap-1">
                <Calendar className="h-3 w-3" />
                فروش ۳۰ روز اخیر
              </p>
              <p className="text-2xl font-bold mt-1 nums">
                {d ? formatRial(d.total_sales) : "—"}
              </p>
              <p className="text-xs opacity-90 mt-0.5">
                {d ? formatNumber(d.total_count) : 0} فاکتور
              </p>
            </div>
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-white/15 backdrop-blur">
              <BarChart3 className="h-7 w-7" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Secondary KPIs */}
      <div className="grid grid-cols-3 gap-2">
        <MiniStat
          icon={<Hash className="h-4 w-4" />}
          label="میانگین فاکتور"
          value={d ? formatRial(d.avg_sale) : "—"}
        />
        <MiniStat
          icon={<Wallet className="h-4 w-4" />}
          label="امانی"
          value={d ? formatNumber(d.consignment_count) : "—"}
          tone="amber"
        />
        <MiniStat
          icon={<Wallet className="h-4 w-4" />}
          label="قطعی"
          value={d ? formatNumber(d.firm_count) : "—"}
          tone="emerald"
        />
      </div>

      {/* List */}
      <div className="space-y-1.5">
        <p className="text-xs font-semibold text-muted-foreground">آخرین فاکتورها:</p>
        {d && d.results.length > 0 ? (
          d.results.slice(0, 8).map((r) => (
            <Card key={r.sale_id} className="border-border/60">
              <CardContent className="p-2.5 flex items-center justify-between">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <p className="text-sm font-bold nums" dir="ltr">{r.sale_no}</p>
                    <span
                      className={cn(
                        "text-[10px] px-1.5 py-0.5 rounded",
                        r.sales_type === "consignment"
                          ? "bg-amber-50 text-amber-700"
                          : "bg-emerald-50 text-emerald-700"
                      )}
                    >
                      {r.sales_type_display}
                    </span>
                  </div>
                  <p className="text-[11px] text-muted-foreground truncate mt-0.5">
                    {r.store_name} · {formatDate(r.sale_date)}
                  </p>
                </div>
                <p className="text-sm font-bold text-emerald-700 nums shrink-0">
                  {formatRial(r.total_amount)}
                </p>
              </CardContent>
            </Card>
          ))
        ) : (
          <p className="text-xs text-center text-muted-foreground py-4">
            هنوز فروشی ثبت نشده است.
          </p>
        )}
      </div>
    </div>
  );
}

function CommissionReport() {
  const { data, isLoading } = useQuery({
    queryKey: ["distributor", "report", "my_commission"],
    queryFn: () => api<MyCommissionReport>("/reports/my_commission/"),
  });

  if (isLoading) return <ReportSkeleton />;
  if (!data) return null;
  const d = data;

  const owed = parseFloat(d.commission_owed);
  const paid = parseFloat(d.commission_paid);
  const balance = parseFloat(d.balance);
  const rate = parseFloat(d.commission_rate);

  return (
    <div className="space-y-3">
      {/* Big card */}
      <Card className="border-amber-200 bg-gradient-to-l from-amber-500 to-orange-500 text-white">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs opacity-90">پورسانت این ماه ({formatNumber(rate)}%)</p>
              <p className="text-2xl font-bold mt-1 nums">{formatRial(owed)}</p>
              <p className="text-xs opacity-90 mt-0.5">
                پرداخت‌شده: {formatRial(paid)}
              </p>
            </div>
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-white/15 backdrop-blur">
              <TrendingUp className="h-7 w-7" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Detail cards */}
      <div className="grid grid-cols-2 gap-2">
        <DetailCard label="نرخ پورسانت" value={`${formatNumber(rate)}%`} icon={<TrendingUp className="h-4 w-4" />} tone="amber" />
        <DetailCard label="جمع فروش" value={formatRial(d.total_sales)} icon={<ShoppingBag className="h-4 w-4" />} tone="emerald" />
        <DetailCard label="پرداخت‌شده" value={formatRial(paid)} icon={<Wallet className="h-4 w-4" />} tone="emerald" />
        <DetailCard
          label="مانده"
          value={formatRial(balance)}
          icon={<Wallet className="h-4 w-4" />}
          tone={balance > 0 ? "amber" : "emerald"}
        />
      </div>

      {/* Distributor info */}
      <Card className="border-border/60">
        <CardContent className="p-3 space-y-1 text-xs">
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">عامل پخش</span>
            <span className="font-medium">{d.distributor_name}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">کد</span>
            <span className="font-medium nums" dir="ltr">{d.distributor_code}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">دوره گزارش</span>
            <span className="font-medium">{formatNumber(d.period_days)} روز اخیر</span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function BalanceReport() {
  const { data, isLoading } = useQuery({
    queryKey: ["distributor", "report", "my_product_balance"],
    queryFn: () => api<MyProductBalanceReport>("/reports/my_product_balance/"),
  });

  if (isLoading) return <ReportSkeleton />;
  if (!data) return null;
  const d = data;

  return (
    <div className="space-y-3">
      {/* Summary */}
      <Card className="border-blue-200 bg-gradient-to-l from-blue-500 to-indigo-500 text-white">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs opacity-90">ارزش کل کالای در دست</p>
              <p className="text-2xl font-bold mt-1 nums">{formatRial(d.total_value)}</p>
              <p className="text-xs opacity-90 mt-0.5">
                {formatNumber(d.total_qty)} کالا در دست
              </p>
            </div>
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-white/15 backdrop-blur">
              <Package className="h-7 w-7" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* List */}
      <div className="space-y-1.5">
        <p className="text-xs font-semibold text-muted-foreground">اقلام کالا:</p>
        {d.results.length > 0 ? (
          d.results.map((p) => {
            const qty = parseFloat(p.qty);
            const price = parseFloat(p.unit_price);
            const total = parseFloat(p.total_value) || qty * price;
            return (
              <Card key={p.product_id} className="border-border/60">
                <CardContent className="p-3">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-start gap-2.5 min-w-0 flex-1">
                      <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-100 text-blue-600 shrink-0">
                        <Package className="h-5 w-5" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-semibold truncate">{p.product_name}</p>
                        <p className="text-[11px] text-muted-foreground nums" dir="ltr">
                          {p.product_code}
                        </p>
                        <div className="flex flex-wrap gap-1 mt-1 text-[10px]">
                          <span className="inline-flex items-center gap-1 rounded bg-amber-50 text-amber-700 px-1.5 py-0.5">
                            <Truck className="h-3 w-3" />
                            {p.dispatch_no}
                          </span>
                          <span className="inline-flex items-center gap-1 rounded bg-muted px-1.5 py-0.5">
                            <Calendar className="h-3 w-3" />
                            {formatDate(p.dispatch_date)}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="text-left shrink-0">
                      <p className="text-sm font-bold text-emerald-700 nums">
                        {formatRial(total)}
                      </p>
                      <p className="text-[11px] text-muted-foreground nums mt-0.5">
                        {formatNumber(qty)} × {formatRial(price)}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })
        ) : (
          <p className="text-xs text-center text-muted-foreground py-4">
            کالایی در دست نیست.
          </p>
        )}
      </div>
    </div>
  );
}

function MiniStat({
  icon,
  label,
  value,
  tone = "default",
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  tone?: "default" | "emerald" | "amber";
}) {
  const toneCls =
    tone === "emerald"
      ? "bg-emerald-50 text-emerald-700"
      : tone === "amber"
      ? "bg-amber-50 text-amber-700"
      : "bg-muted text-muted-foreground";
  return (
    <div className={cn("rounded-xl p-2 text-center", toneCls)}>
      <div className="flex items-center justify-center">
        {icon}
      </div>
      <p className="text-[10px] mt-1 opacity-80">{label}</p>
      <p className="text-xs font-bold nums mt-0.5 truncate">{value}</p>
    </div>
  );
}

function DetailCard({
  label,
  value,
  icon,
  tone,
}: {
  label: string;
  value: string;
  icon: React.ReactNode;
  tone: "emerald" | "amber";
}) {
  const toneCls =
    tone === "emerald"
      ? "bg-emerald-50 text-emerald-700"
      : "bg-amber-50 text-amber-700";
  return (
    <Card className={cn("border-0", toneCls)}>
      <CardContent className="p-3">
        <div className="flex items-center gap-1.5 mb-1 opacity-80">
          {icon}
          <span className="text-[11px]">{label}</span>
        </div>
        <p className="text-sm font-bold nums truncate">{value}</p>
      </CardContent>
    </Card>
  );
}

function ReportSkeleton() {
  return (
    <div className="space-y-3">
      <Skeleton className="h-24 w-full rounded-2xl" />
      <div className="grid grid-cols-3 gap-2">
        <Skeleton className="h-16 rounded-xl" />
        <Skeleton className="h-16 rounded-xl" />
        <Skeleton className="h-16 rounded-xl" />
      </div>
      <Skeleton className="h-32 w-full rounded-2xl" />
    </div>
  );
}
