"use client";

import * as React from "react";
import { CalendarRange } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { todayISO, addDaysISO, formatDate } from "@/lib/calendar";
import { DatePicker } from "@/components/dialogs/datepicker";

export interface DateRangeValue {
  from: string | null;  // ISO YYYY-MM-DD
  to: string | null;     // ISO YYYY-MM-DD
}

interface DateRangeFilterProps {
  value: DateRangeValue;
  onChange: (v: DateRangeValue) => void;
  className?: string;
  /**
   * If `true`, the quick-filter chips are visible. Default: true.
   */
  showQuickFilters?: boolean;
}

interface QuickFilter {
  key: string;
  label: string;
  calc: () => DateRangeValue;
}

const QUICK_FILTERS: QuickFilter[] = [
  {
    key: "today",
    label: "امروز",
    calc: () => {
      const t = todayISO();
      return { from: t, to: t };
    },
  },
  {
    key: "this-week",
    label: "هفته جاری",
    calc: () => {
      const today = new Date();
      const day = today.getDay(); // 0=Sun, 6=Sat
      // Iranian week starts on Saturday (day=6 in JS getDay())
      // Move so Saturday is start of week
      const offsetToSaturday = (day === 6) ? 0 : (day + 1);
      const from = new Date(today);
      from.setDate(today.getDate() - offsetToSaturday);
      const to = new Date(today);
      return {
        from: from.toISOString().slice(0, 10),
        to: to.toISOString().slice(0, 10),
      };
    },
  },
  {
    key: "this-month",
    label: "ماه جاری",
    calc: () => {
      const today = new Date();
      const from = new Date(today.getFullYear(), today.getMonth(), 1);
      return {
        from: from.toISOString().slice(0, 10),
        to: today.toISOString().slice(0, 10),
      };
    },
  },
  {
    key: "this-year",
    label: "سال جاری",
    calc: () => {
      const today = new Date();
      const from = new Date(today.getFullYear(), 0, 1);
      return {
        from: from.toISOString().slice(0, 10),
        to: today.toISOString().slice(0, 10),
      };
    },
  },
  {
    key: "last-7-days",
    label: "۷ روز اخیر",
    calc: () => {
      const t = todayISO();
      return { from: addDaysISO(t, -7) ?? t, to: t };
    },
  },
  {
    key: "last-30-days",
    label: "۳۰ روز اخیر",
    calc: () => {
      const t = todayISO();
      return { from: addDaysISO(t, -30) ?? t, to: t };
    },
  },
];

/**
 * DateRangeFilter — یک ابزارک کوچک برای انتخاب بازه‌ی زمانی.
 * شامل دو DatePicker (from / to) و فیلترهای سریع.
 *
 * تاریخ‌های داخلی ISO (YYYY-MM-DD) هستند و onChange با همین فرمت صدا زده می‌شود.
 * کامپوننت API فرانت‌اند مسئول تبدیل به پارامترهای URL (مثلاً ?start_date=...&end_date=...) است.
 */
export function DateRangeFilter({
  value,
  onChange,
  className,
  showQuickFilters = true,
}: DateRangeFilterProps) {
  const activeKey = React.useMemo(() => {
    if (!value.from || !value.to) return null;
    for (const f of QUICK_FILTERS) {
      const r = f.calc();
      if (r.from === value.from && r.to === value.to) return f.key;
    }
    return null;
  }, [value]);

  return (
    <div className={cn("rounded-lg border bg-card/40 p-3", className)}>
      <div className="flex flex-wrap items-end gap-3">
        <div className="space-y-1.5">
          <p className="text-[11px] font-medium text-muted-foreground">از تاریخ</p>
          <DatePicker
            value={value.from}
            onChange={(iso) => onChange({ ...value, from: iso })}
            placeholder="از تاریخ"
          />
        </div>
        <div className="space-y-1.5">
          <p className="text-[11px] font-medium text-muted-foreground">تا تاریخ</p>
          <DatePicker
            value={value.to}
            onChange={(iso) => onChange({ ...value, to: iso })}
            placeholder="تا تاریخ"
          />
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onChange({ from: null, to: null })}
        >
          پاک‌کردن
        </Button>
      </div>
      {showQuickFilters && (
        <div className="mt-3 flex flex-wrap items-center gap-1.5">
          <span className="text-[11px] text-muted-foreground flex items-center gap-1">
            <CalendarRange className="h-3 w-3" /> فیلتر سریع:
          </span>
          {QUICK_FILTERS.map((f) => (
            <button
              key={f.key}
              type="button"
              onClick={() => onChange(f.calc())}
              className={cn(
                "rounded-full border px-2.5 py-1 text-[11px] font-medium transition-colors",
                activeKey === f.key
                  ? "border-primary bg-primary/10 text-primary"
                  : "border-border text-muted-foreground hover:bg-muted/60"
              )}
            >
              {f.label}
            </button>
          ))}
        </div>
      )}
      {(value.from || value.to) && (
        <p className="mt-2 text-[11px] text-muted-foreground nums" dir="ltr">
          {value.from ? formatDate(value.from) : "—"} ← {value.to ? formatDate(value.to) : "—"}
        </p>
      )}
    </div>
  );
}

/**
 * Build URL query params `{ start_date, end_date }` from a DateRangeValue,
 * omitting null values.
 */
export function rangeToQuery(v: DateRangeValue): Record<string, string> {
  const out: Record<string, string> = {};
  if (v.from) out.start_date = v.from;
  if (v.to) out.end_date = v.to;
  return out;
}

export const DEFAULT_RANGE: DateRangeValue = {
  from: addDaysISO(todayISO(), -30),
  to: todayISO(),
};
