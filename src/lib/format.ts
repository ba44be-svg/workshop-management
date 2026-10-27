// Formatting helpers — Persian/Farsi friendly.
// Date formatting delegates to the dual-calendar system in `@/lib/calendar.ts`
// so views automatically render in شمسی/میلادی based on the user's setting.

import { formatDate as calFormatDate, formatDateTime as calFormatDateTime, getCalendarMode } from "@/lib/calendar";

const numberFormatter = new Intl.NumberFormat("en-US", {
  maximumFractionDigits: 2,
});

export function formatNumber(value: number | string | null | undefined): string {
  if (value === null || value === undefined || value === "") return "—";
  const n = typeof value === "string" ? parseFloat(value) : value;
  if (Number.isNaN(n)) return String(value);
  return numberFormatter.format(n);
}

export function formatRial(value: number | string | null | undefined): string {
  const n =
    typeof value === "string" ? parseFloat(value) : (value as number) || 0;
  if (Number.isNaN(n)) return "—";
  return `${numberFormatter.format(Math.round(n))} ریال`;
}

export function formatQty(value: number | string | null | undefined): string {
  const n =
    typeof value === "string" ? parseFloat(value) : (value as number) || 0;
  if (Number.isNaN(n)) return "—";
  return numberFormatter.format(n);
}

// formatDate / formatDateTime now read the active calendar mode (jalali/gregorian)
// from localStorage. The mode defaults to jalali (شمسی) for new users.

export function formatDate(input: string | Date | null | undefined): string {
  return calFormatDate(input, getCalendarMode());
}

export function formatDateTime(input: string | Date | null | undefined): string {
  return calFormatDateTime(input, getCalendarMode());
}

export function daysUntil(input: string | Date | null | undefined): number | null {
  if (!input) return null;
  const d = typeof input === "string" ? new Date(input) : input;
  if (Number.isNaN(d.getTime())) return null;
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  const target = new Date(d);
  target.setHours(0, 0, 0, 0);
  const diff = target.getTime() - now.getTime();
  return Math.round(diff / (1000 * 60 * 60 * 24));
}

export function relativeTime(input: string | Date | null | undefined): string {
  if (!input) return "—";
  const d = typeof input === "string" ? new Date(input) : input;
  if (Number.isNaN(d.getTime())) return String(input);
  const diff = Date.now() - d.getTime();
  const min = Math.round(diff / 60000);
  if (min < 1) return "هم‌اکنون";
  if (min < 60) return `${min} دقیقه پیش`;
  const hr = Math.round(min / 60);
  if (hr < 24) return `${hr} ساعت پیش`;
  const day = Math.round(hr / 24);
  if (day < 30) return `${day} روز پیش`;
  return formatDate(d);
}

// Re-export the dual-calendar helpers so existing imports from "@/lib/format"
// that want the calendar-aware variants can grab them from one place.
export { calFormatDate, calFormatDateTime };
