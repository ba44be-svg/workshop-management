// Dual-calendar helpers — supports Jalali (Persian شمسی) and Gregorian (میلادی).
// The active mode is persisted to localStorage under `workshop_calendar`.
// All formatting / parsing goes through this module so views stay agnostic
// of which calendar the operator has chosen.

export type CalendarMode = "jalali" | "gregorian";

const STORAGE_KEY = "workshop_calendar";

export function getCalendarMode(): CalendarMode {
  if (typeof window === "undefined") return "jalali";
  const v = window.localStorage.getItem(STORAGE_KEY);
  return v === "gregorian" ? "gregorian" : "jalali";
}

export function setCalendarMode(mode: CalendarMode): void {
  if (typeof window !== "undefined") {
    window.localStorage.setItem(STORAGE_KEY, mode);
  }
}

// --- Gregorian ⇄ Jalali conversion (algorithm by Kazimierz M. Borkowski) ---
// Based on the well-known two-step leap-year rule. Returns Gregorian date parts.

function div(a: number, b: number): number {
  return Math.floor(a / b);
}

function gregorianToJalali(gy: number, gm: number, gd: number): { jy: number; jm: number; jd: number } {
  const g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334];
  const gy2 = gm > 2 ? gy + 1 : gy;
  const days =
    355666 +
    365 * gy +
    div(gy2 + 3, 4) -
    div(gy2 + 99, 100) +
    div(gy2 + 399, 400) +
    gd +
    g_d_m[gm - 1];
  const jy = -1595 + 33 * div(days, 12053);
  const r = days % 12053;
  if (r < 365) {
    // r is day-of-year in Jalali
    const jm = r < 186 ? Math.ceil((r + 1) / 31) : Math.ceil((r - 186 + 1) / 30) + 6;
    const jd = r < 186 ? (r % 31) + 1 : ((r - 186) % 30) + 1;
    return { jy, jm, jd };
  }
  // r >= 365: leap-day extension
  const jy2 = jy + 1 + div(r - 1, 365);
  const r2 = (r - 1) % 365;
  const jm = r2 < 186 ? Math.ceil((r2 + 1) / 31) : Math.ceil((r2 - 186 + 1) / 30) + 6;
  const jd = r2 < 186 ? (r2 % 31) + 1 : ((r2 - 186) % 30) + 1;
  return { jy: jy2, jm, jd };
}

function jalaliToGregorian(jy: number, jm: number, jd: number): { y: number; m: number; d: number } {
  const jy2 = jy > 0 ? jy - 1 : jy;
  const days =
    365 * jy +
    div(jy2, 33) * 8 +
    div((jy2 % 33) + 3, 4) +
    jd +
    (jm < 7 ? (jm - 1) * 31 : (jm - 7) * 30 + 186);
  let gy = 1595 + 33 * div(days, 12053);
  let r = days % 12053;
  if (r < 365) {
    const g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334];
    let gm = 0;
    for (let i = 0; i < 12; i++) {
      if (g_d_m[i] + ((gy % 4 === 0 && gy % 100 !== 0) || gy % 400 === 0 ? 1 : 0) > r) {
        gm = i;
        break;
      }
      gm = 12;
    }
    // simpler: walk months
    gm = 1;
    let remaining = r;
    const leap = (gy % 4 === 0 && gy % 100 !== 0) || gy % 400 === 0;
    for (let i = 0; i < 12; i++) {
      const ml = [31, leap ? 30 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][i];
      if (remaining < ml) {
        gm = i + 1;
        return { y: gy, m: gm, d: remaining + 1 };
      }
      remaining -= ml;
    }
    return { y: gy, m: 12, d: 31 };
  }
  gy += 1 + div(r - 1, 365);
  r = (r - 1) % 365;
  const leap = (gy % 4 === 0 && gy % 100 !== 0) || gy % 400 === 0;
  let gm = 1;
  let remaining = r;
  for (let i = 0; i < 12; i++) {
    const ml = [31, leap ? 30 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][i];
    if (remaining < ml) {
      gm = i + 1;
      return { y: gy, m: gm, d: remaining + 1 };
    }
    remaining -= ml;
  }
  return { y: gy, m: 12, d: 31 };
}

// --- Public formatting ---

/** Format a date string (ISO or Date) for display in the active calendar mode. */
export function formatDate(input: string | Date | null | undefined, mode?: CalendarMode): string {
  if (!input) return "—";
  const d = typeof input === "string" ? new Date(input) : input;
  if (Number.isNaN(d.getTime())) return String(input);
  const m = mode ?? getCalendarMode();
  if (m === "jalali") {
    try {
      return new Intl.DateTimeFormat("fa-IR-u-ca-persian", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
      }).format(d);
    } catch {
      // Fallback: manual conversion
      const j = gregorianToJalali(d.getFullYear(), d.getMonth() + 1, d.getDate());
      return `${j.jy}/${String(j.jm).padStart(2, "0")}/${String(j.jd).padStart(2, "0")}`;
    }
  }
  // Gregorian ISO-style
  const y = d.getFullYear();
  const mo = String(d.getMonth() + 1).padStart(2, "0");
  const da = String(d.getDate()).padStart(2, "0");
  return `${y}-${mo}-${da}`;
}

/** Format with date + HH:mm. */
export function formatDateTime(input: string | Date | null | undefined, mode?: CalendarMode): string {
  if (!input) return "—";
  const d = typeof input === "string" ? new Date(input) : input;
  if (Number.isNaN(d.getTime())) return String(input);
  const date = formatDate(d, mode);
  const hh = String(d.getHours()).padStart(2, "0");
  const mm = String(d.getMinutes()).padStart(2, "0");
  return `${date} ${hh}:${mm}`;
}

/**
 * Convert a user-entered date string to ISO (YYYY-MM-DD) for the backend.
 * In jalali mode the input is `YYYY/MM/DD` (e.g. `1403/08/01`).
 * In gregorian mode the input is `YYYY-MM-DD` or `YYYY/MM/DD`.
 */
export function parseInputDate(value: string, mode?: CalendarMode): string | null {
  if (!value) return null;
  const m = mode ?? getCalendarMode();
  try {
    if (m === "jalali") {
      const cleaned = value.trim().replace(/-/g, "/");
      const parts = cleaned.split("/").map((p) => parseInt(p, 10));
      if (parts.length !== 3 || parts.some((n) => Number.isNaN(n))) return null;
      const [jy, jm, jd] = parts;
      const g = jalaliToGregorian(jy, jm, jd);
      const dt = new Date(Date.UTC(g.y, g.m - 1, g.d));
      return dt.toISOString().slice(0, 10);
    }
    // Gregorian: accept `YYYY-MM-DD` or `YYYY/MM/DD`
    const cleaned = value.trim().replace(/\//g, "-");
    const parts = cleaned.split("-").map((p) => parseInt(p, 10));
    if (parts.length !== 3 || parts.some((n) => Number.isNaN(n))) return null;
    const [y, mo, d] = parts;
    const dt = new Date(Date.UTC(y, mo - 1, d));
    return dt.toISOString().slice(0, 10);
  } catch {
    return null;
  }
}

/** Today's date as a display string in the current mode. */
export function today(mode?: CalendarMode): string {
  return formatDate(new Date(), mode);
}

/** Today's date as ISO YYYY-MM-DD. */
export function todayISO(): string {
  return new Date().toISOString().slice(0, 10);
}

/** Convert an ISO date to the display string in the current mode. Alias of formatDate. */
export function isoToDisplay(iso: string | null | undefined, mode?: CalendarMode): string {
  return formatDate(iso, mode);
}

/** Convert an ISO date to a user-input string in the current mode (for <input>). */
export function isoToInput(iso: string | null | undefined, mode?: CalendarMode): string {
  if (!iso) return "";
  const m = mode ?? getCalendarMode();
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  if (m === "jalali") {
    const j = gregorianToJalali(d.getFullYear(), d.getMonth() + 1, d.getDate());
    return `${j.jy}/${String(j.jm).padStart(2, "0")}/${String(j.jd).padStart(2, "0")}`;
  }
  const y = d.getFullYear();
  const mo = String(d.getMonth() + 1).padStart(2, "0");
  const da = String(d.getDate()).padStart(2, "0");
  return `${y}-${mo}-${da}`;
}

/** Add N days to an ISO date string and return ISO YYYY-MM-DD. */
export function addDaysISO(iso: string | null | undefined, days: number): string | null {
  if (!iso) return null;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return null;
  d.setDate(d.getDate() + days);
  return d.toISOString().slice(0, 10);
}

export { gregorianToJalali, jalaliToGregorian };
