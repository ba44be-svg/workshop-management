"use client";

import * as React from "react";
import { CalendarIcon, ChevronRight, ChevronLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import {
  formatDate,
  parseInputDate,
  isoToInput,
  todayISO,
  getCalendarMode,
  type CalendarMode,
} from "@/lib/calendar";

interface DatePickerProps {
  value?: string | null;
  onChange: (iso: string | null) => void;
  mode?: CalendarMode;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
}

// ─── تبدیل میلادی به شمسی (الگوریتم Borkowski) ─────────────────────────
function gregorianToJalali(gy: number, gm: number, gd: number): [number, number, number] {
  const g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334];
  let jy = (gy <= 1600) ? 0 : 979;
  gy -= (gy <= 1600) ? 621 : 1600;
  let gy2 = (gm > 2) ? (gy + 1) : gy;
  let days = (365 * gy) + (Math.floor((gy2 + 3) / 4)) - (Math.floor((gy2 + 99) / 100)) + (Math.floor((gy2 + 399) / 400)) - 80 + gd + g_d_m[gm - 1];
  jy += 33 * Math.floor(days / 12053);
  days %= 12053;
  jy += 4 * Math.floor(days / 1461);
  days %= 1461;
  if (days > 365) {
    jy += Math.floor((days - 1) / 365);
    days = (days - 1) % 365;
  }
  const jm = (days < 186) ? 1 + Math.floor(days / 31) : 7 + Math.floor((days - 186) / 30);
  const jd = 1 + ((days < 186) ? (days % 31) : ((days - 186) % 30));
  return [jy, jm, jd];
}

// ─── تبدیل شمسی به میلادی ──────────────────────────────────────────────
function jalaliToGregorian(jy: number, jm: number, jd: number): [number, number, number] {
  let gy = (jy <= 979) ? 621 : 1600;
  jy -= (jy <= 979) ? 0 : 979;
  let days = (365 * jy) + (Math.floor(jy / 33) * 8) + (Math.floor((jy % 33 + 3) / 4)) + 78 + jd + ((jm < 7) ? (jm - 1) * 31 : ((jm - 7) * 30) + 186);
  gy += 400 * Math.floor(days / 146097);
  days %= 146097;
  if (days > 36524) {
    gy += 100 * Math.floor(--days / 36524);
    days %= 36524;
    if (days >= 365) days++;
  }
  gy += 4 * Math.floor(days / 1461);
  days %= 1461;
  if (days > 365) {
    gy += Math.floor((days - 1) / 365);
    days = (days - 1) % 365;
  }
  let gd = days + 1;
  const sal_a = [0, 31, ((gy % 4 === 0 && gy % 100 !== 0) || (gy % 400 === 0)) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  let gm = 0;
  for (gm = 0; gm < 13 && gd > sal_a[gm]; gm++) gd -= sal_a[gm];
  return [gy, gm, gd];
}

// ─── نام‌های فارسی ─────────────────────────────────────────────────────
const JALALI_MONTHS = [
  "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
  "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
];
const JALALI_WEEKDAYS = ["ش", "ی", "د", "س", "چ", "پ", "ج"];

function toPersianDigits(n: number | string): string {
  const persian = ["۰", "۱", "۲", "۳", "۴", "۵", "۶", "۷", "۸", "۹"];
  return String(n).replace(/\d/g, (d) => persian[parseInt(d)]);
}

// ─── DatePicker کامپوننت ───────────────────────────────────────────────
export function DatePicker({
  value,
  onChange,
  mode,
  placeholder = "انتخاب تاریخ",
  disabled,
  className,
}: DatePickerProps) {
  const [open, setOpen] = React.useState(false);
  const m = mode ?? getCalendarMode();
  const isoValue = value ?? null;
  const dateObj = isoValue ? new Date(isoValue + "T00:00:00") : undefined;
  const display = isoValue ? formatDate(isoValue, m) : placeholder;
  const isJalali = m === "jalali";

  // محاسبه‌ی ماه/سال فعلی برای نمایش در تقویم شمسی
  const [viewYear, setViewYear] = React.useState<number>(() => {
    if (!dateObj) {
      const now = new Date();
      const [jy] = gregorianToJalali(now.getFullYear(), now.getMonth() + 1, now.getDate());
      return jy;
    }
    const [jy] = gregorianToJalali(dateObj.getFullYear(), dateObj.getMonth() + 1, dateObj.getDate());
    return jy;
  });
  const [viewMonth, setViewMonth] = React.useState<number>(() => {
    if (!dateObj) {
      const now = new Date();
      const [, jm] = gregorianToJalali(now.getFullYear(), now.getMonth() + 1, now.getDate());
      return jm - 1; // 0-indexed
    }
    const [, jm] = gregorianToJalali(dateObj.getFullYear(), dateObj.getMonth() + 1, dateObj.getDate());
    return jm - 1;
  });

  // محاسبه‌ی روزهای ماه شمسی
  const daysInJalaliMonth = (year: number, month: number): number => {
    if (month <= 5) return 31; // فروردین تا شهریور
    if (month <= 10) return 30; // مهر تا اسفند
    // اسفند
    const [gy, gm, gd] = jalaliToGregorian(year, 12, 1);
    const isLeap = ((gy % 4 === 0 && gy % 100 !== 0) || (gy % 400 === 0));
    return isLeap ? 30 : 29;
  };

  // محاسبه‌ی روز هفته‌ی اول ماه (0=شنبه)
  const firstDayOfWeek = (year: number, month: number): number => {
    const [gy, gm, gd] = jalaliToGregorian(year, month + 1, 1);
    const date = new Date(gy, gm - 1, gd);
    // در تقویم شمسی: شنبه=0, یکشنبه=1, ..., جمعه=6
    // در JS: یکشنبه=0, ..., جمعه=6
    const jsDay = date.getDay();
    return (jsDay + 1) % 7;
  };

  // روزهای ماه
  const days: (number | null)[] = [];
  const totalDays = daysInJalaliMonth(viewYear, viewMonth);
  const firstDay = firstDayOfWeek(viewYear, viewMonth);
  for (let i = 0; i < firstDay; i++) days.push(null);
  for (let i = 1; i <= totalDays; i++) days.push(i);
  while (days.length % 7 !== 0) days.push(null);

  // روز انتخاب‌شده (شمسی)
  const selectedJalali = dateObj
    ? gregorianToJalali(dateObj.getFullYear(), dateObj.getMonth() + 1, dateObj.getDate())
    : null;

  // امروز (شمسی)
  const now = new Date();
  const todayJalali = gregorianToJalali(now.getFullYear(), now.getMonth() + 1, now.getDate());

  // انتخاب روز
  const handleDayClick = (day: number) => {
    const [gy, gm, gd] = jalaliToGregorian(viewYear, viewMonth + 1, day);
    const iso = `${gy}-${String(gm).padStart(2, "0")}-${String(gd).padStart(2, "0")}`;
    onChange(iso);
    setOpen(false);
  };

  // ماه قبل/بعد
  const prevMonth = () => {
    if (viewMonth === 0) {
      setViewMonth(11);
      setViewYear((y) => y - 1);
    } else {
      setViewMonth((m) => m - 1);
    }
  };
  const nextMonth = () => {
    if (viewMonth === 11) {
      setViewMonth(0);
      setViewYear((y) => y + 1);
    } else {
      setViewMonth((m) => m + 1);
    }
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          type="button"
          variant="outline"
          disabled={disabled}
          className={cn(
            "w-full justify-start text-right font-normal nums",
            !isoValue && "text-muted-foreground",
            className
          )}
          dir="ltr"
        >
          <CalendarIcon className="ml-2 h-4 w-4" />
          <span dir="rtl">{display}</span>
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0" align="start" dir="rtl">
        {isJalali ? (
          // ─── تقویم شمسی ────────────────────────────────────────────
          <div className="p-3 w-[280px]">
            {/* هدر: ماه + سال + ناوبری */}
            <div className="flex items-center justify-between mb-3">
              <Button variant="ghost" size="icon" onClick={prevMonth} className="h-7 w-7">
                <ChevronRight className="h-4 w-4" />
              </Button>
              <div className="flex items-center gap-2">
                <select
                  value={viewMonth}
                  onChange={(e) => setViewMonth(Number(e.target.value))}
                  className="text-sm border rounded px-1 py-0.5 bg-background"
                >
                  {JALALI_MONTHS.map((month, i) => (
                    <option key={i} value={i}>{month}</option>
                  ))}
                </select>
                <select
                  value={viewYear}
                  onChange={(e) => setViewYear(Number(e.target.value))}
                  className="text-sm border rounded px-1 py-0.5 bg-background nums"
                >
                  {Array.from({ length: 20 }, (_, i) => viewYear - 10 + i).map((y) => (
                    <option key={y} value={y}>{toPersianDigits(y)}</option>
                  ))}
                </select>
              </div>
              <Button variant="ghost" size="icon" onClick={nextMonth} className="h-7 w-7">
                <ChevronLeft className="h-4 w-4" />
              </Button>
            </div>

            {/* روزهای هفته */}
            <div className="grid grid-cols-7 gap-1 mb-1">
              {JALALI_WEEKDAYS.map((day, i) => (
                <div key={i} className="text-center text-[11px] text-muted-foreground font-medium h-8 flex items-center justify-center">
                  {day}
                </div>
              ))}
            </div>

            {/* روزهای ماه */}
            <div className="grid grid-cols-7 gap-1">
              {days.map((day, i) => {
                if (day === null) return <div key={i} />;
                const isToday = todayJalali[0] === viewYear && todayJalali[1] === viewMonth + 1 && todayJalali[2] === day;
                const isSelected = selectedJalali && selectedJalali[0] === viewYear && selectedJalali[1] === viewMonth + 1 && selectedJalali[2] === day;
                return (
                  <button
                    key={i}
                    type="button"
                    onClick={() => handleDayClick(day)}
                    className={cn(
                      "h-8 w-8 rounded-md text-sm transition-colors hover:bg-accent",
                      isSelected && "bg-primary text-primary-foreground hover:bg-primary",
                      !isSelected && isToday && "ring-1 ring-primary",
                      !isSelected && !isToday && "text-foreground"
                    )}
                  >
                    {toPersianDigits(day)}
                  </button>
                );
              })}
            </div>
          </div>
        ) : (
          // ─── تقویم میلادی (ساده) ──────────────────────────────────
          <div className="p-3 w-[280px]">
            <div className="flex items-center justify-between mb-3">
              <Button variant="ghost" size="icon" onClick={() => setViewMonth((m) => (m === 0 ? 11 : m - 1))} className="h-7 w-7">
                <ChevronRight className="h-4 w-4" />
              </Button>
              <span className="text-sm font-medium">
                {dateObj?.toLocaleString("default", { month: "long", year: "numeric" }) ?? new Date().toLocaleString("default", { month: "long", year: "numeric" })}
              </span>
              <Button variant="ghost" size="icon" onClick={() => setViewMonth((m) => (m === 11 ? 0 : m + 1))} className="h-7 w-7">
                <ChevronLeft className="h-4 w-4" />
              </Button>
            </div>
            <p className="text-center text-sm text-muted-foreground">
              برای تقویم میلادی، از ورودی دستی زیر استفاده کنید.
            </p>
          </div>
        )}

        {/* ورودی دستی */}
        <div className="flex items-center justify-between gap-2 border-t px-3 py-2 text-xs">
          <span className="text-muted-foreground">
            {isJalali ? "ورودی شمسی:" : "ورودی میلادی:"}
          </span>
          <input
            type="text"
            dir="ltr"
            className="flex-1 rounded border bg-background px-2 py-1 text-xs nums"
            placeholder={isJalali ? "1403/08/01" : "2024-10-25"}
            defaultValue={isoValue ? isoToInput(isoValue, m) : ""}
            onChange={(e) => {
              const iso = parseInputDate(e.target.value, m);
              if (iso) onChange(iso);
            }}
          />
          <Button
            type="button"
            size="sm"
            variant="outline"
            onClick={() => {
              onChange(todayISO());
              setOpen(false);
            }}
          >
            امروز
          </Button>
        </div>
      </PopoverContent>
    </Popover>
  );
}
