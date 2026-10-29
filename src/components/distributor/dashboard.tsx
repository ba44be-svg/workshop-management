"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  Package,
  ShoppingCart,
  Wallet,
  TrendingUp,
  Plus,
  BarChart3,
  ArrowLeft,
  Calendar,
} from "lucide-react";
import { api } from "@/lib/api";
import { useDistributorAuthStore } from "@/store/distributor-auth-store";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { formatRial, formatNumber, formatDate } from "@/lib/format";
import type { DistributorTab } from "@/components/distributor/distributor-app";

interface DashboardData {
  products_count: number;
  products_value: string;
  today_sales_count: number;
  today_sales_value: string;
  commission_this_month: string;
  commission_paid: string;
  balance: string;
}

export function DistributorDashboard({
  onGoto,
}: {
  onGoto: (t: DistributorTab) => void;
}) {
  const { user } = useDistributorAuthStore();

  // Pull my_sales + product balance + commission, aggregate to dashboard cards.
  const { data: salesRes, isLoading: salesLoading } = useQuery({
    queryKey: ["distributor", "my_sales"],
    queryFn: () =>
      api<{
        count: number;
        results: Array<{ sale_date: string; total_amount: string }>;
      }>("/sales/my_sales/"),
  });

  const { data: productsRes, isLoading: productsLoading } = useQuery({
    queryKey: ["distributor", "my_dispatches"],
    queryFn: () =>
      api<{
        count: number;
        results: Array<{
          id: number;
          dispatch_no: string;
          total_amount: string;
          lines: Array<{ qty: string; line_total: string }>;
        }>;
      }>("/dispatch/my_dispatches/"),
  });

  const { data: commissionRes, isLoading: commissionLoading } = useQuery({
    queryKey: ["distributor", "commission"],
    queryFn: () =>
      api<{
        commission_rate: string;
        total_sales: string;
        commission_owed: string;
        commission_paid: string;
        balance: string;
      }>("/reports/my_commission/"),
  });

  // Aggregate
  const today = new Date().toISOString().slice(0, 10);
  const todaySales = (salesRes?.results ?? []).filter(
    (s) => s.sale_date === today
  );
  const productsFlattened = (productsRes?.results ?? []).flatMap((d) =>
    (d.lines ?? []).map((l) => ({
      qty: parseFloat(l.qty ?? "0"),
      total: parseFloat(l.line_total ?? "0"),
    }))
  );
  const productsCount = productsFlattened.length;
  const productsValue = productsFlattened.reduce((s, p) => s + p.total, 0);

  const data: DashboardData = {
    products_count: productsCount,
    products_value: String(productsValue) + ".0000",
    today_sales_count: todaySales.length,
    today_sales_value:
      String(todaySales.reduce((s, x) => s + parseFloat(x.total_amount), 0)) +
      ".0000",
    commission_this_month: commissionRes?.commission_owed ?? "0.0000",
    commission_paid: commissionRes?.commission_paid ?? "0.0000",
    balance: commissionRes?.balance ?? "0.0000",
  };

  const loading = salesLoading || productsLoading || commissionLoading;

  return (
    <div className="space-y-4">
      {/* Welcome banner */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-2xl bg-gradient-to-l from-emerald-600 to-teal-600 p-4 text-white shadow-lg"
      >
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs opacity-90">سلام 👋</p>
            <p className="text-lg font-bold">
              {user?.display_name ?? "عامل پخش"}
            </p>
            <p className="text-xs opacity-90 mt-0.5 flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              {formatDate(today)}
            </p>
          </div>
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white/15 backdrop-blur">
            <BarChart3 className="h-6 w-6" />
          </div>
        </div>
      </motion.div>

      {/* KPI cards */}
      <div className="grid grid-cols-2 gap-3">
        <KpiCard
          title="تعداد کالای در دست"
          value={loading ? null : formatNumber(data.products_count)}
          icon={<Package className="h-5 w-5" />}
          color="from-blue-500 to-indigo-500"
          onClick={() => onGoto("products")}
        />
        <KpiCard
          title="فروش امروز"
          value={loading ? null : `${formatNumber(data.today_sales_count)} فاکتور`}
          subtitle={
            loading ? undefined : formatRial(data.today_sales_value)
          }
          icon={<ShoppingCart className="h-5 w-5" />}
          color="from-emerald-500 to-teal-500"
          onClick={() => onGoto("sales")}
        />
        <KpiCard
          title="پورسانت این ماه"
          value={loading ? null : formatRial(data.commission_this_month)}
          subtitle={loading ? undefined : `پرداخت‌شده: ${formatRial(data.commission_paid)}`}
          icon={<TrendingUp className="h-5 w-5" />}
          color="from-amber-500 to-orange-500"
          onClick={() => onGoto("reports")}
        />
        <KpiCard
          title="مانده حساب"
          value={loading ? null : formatRial(data.balance)}
          subtitle="طلب کارفرما"
          icon={<Wallet className="h-5 w-5" />}
          color="from-purple-500 to-fuchsia-500"
          onClick={() => onGoto("reports")}
        />
      </div>

      {/* Quick action buttons */}
      <div className="grid grid-cols-2 gap-3 pt-1">
        <Button
          onClick={() => onGoto("new-sale")}
          className="h-14 text-base bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700"
        >
          <Plus className="h-5 w-5 ml-2" />
          فروش جدید
        </Button>
        <Button
          onClick={() => onGoto("reports")}
          variant="outline"
          className="h-14 text-base border-emerald-300 text-emerald-700 hover:bg-emerald-50"
        >
          <BarChart3 className="h-5 w-5 ml-2" />
          گزارش‌ها
        </Button>
      </div>

      {/* Recent activity quick links */}
      <Card className="border-emerald-100">
        <CardContent className="p-3 space-y-1">
          <button
            onClick={() => onGoto("products")}
            className="flex w-full items-center justify-between rounded-lg px-2 py-2.5 text-right hover:bg-emerald-50 transition-colors"
          >
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-100 text-blue-600">
                <Package className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm font-medium">کالاهای در دست</p>
                <p className="text-xs text-muted-foreground">
                  {loading ? "در حال بارگذاری…" : `${formatNumber(data.products_count)} قلم کالا`}
                </p>
              </div>
            </div>
            <ArrowLeft className="h-4 w-4 text-muted-foreground" />
          </button>
          <div className="h-px bg-border/60" />
          <button
            onClick={() => onGoto("sales")}
            className="flex w-full items-center justify-between rounded-lg px-2 py-2.5 text-right hover:bg-emerald-50 transition-colors"
          >
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-100 text-emerald-600">
                <ShoppingCart className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm font-medium">فاکتورهای اخیر</p>
                <p className="text-xs text-muted-foreground">
                  {loading
                    ? "در حال بارگذاری…"
                    : `${formatNumber(salesRes?.count ?? 0)} فاکتور ثبت‌شده`}
                </p>
              </div>
            </div>
            <ArrowLeft className="h-4 w-4 text-muted-foreground" />
          </button>
        </CardContent>
      </Card>
    </div>
  );
}

function KpiCard({
  title,
  value,
  subtitle,
  icon,
  color,
  onClick,
}: {
  title: string;
  value: string | null;
  subtitle?: string;
  icon: React.ReactNode;
  color: string;
  onClick?: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="text-right rounded-2xl border bg-white p-3 shadow-sm hover:shadow-md transition-all hover:-translate-y-0.5"
    >
      <div className={`mb-2 flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br ${color} text-white shadow`}>
        {icon}
      </div>
      <p className="text-[11px] text-muted-foreground leading-tight">{title}</p>
      {value === null ? (
        <Skeleton className="mt-1 h-5 w-20" />
      ) : (
        <p className="text-sm font-bold nums leading-tight mt-0.5">{value}</p>
      )}
      {subtitle && (
        <p className="text-[10px] text-muted-foreground mt-0.5 nums">{subtitle}</p>
      )}
    </button>
  );
}
