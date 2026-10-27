"use client";
import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { Factory, Boxes, Package, type LucideIcon } from "lucide-react";
import type { CalendarMode } from "@/lib/calendar";
import type { ThemeKey } from "@/lib/themes";

export type IconKey = "factory" | "boxes" | "package";
export type Layout = "sidebar-right" | "sidebar-left" | "topbar";
export type Theme = ThemeKey;

export const ICON_MAP: Record<string, LucideIcon> = { factory: Factory, boxes: Boxes, package: Package };

interface ConfigState {
  title: string;
  iconKey: IconKey;
  theme: Theme;
  layout: Layout;
  calendarMode: CalendarMode;
  brandColor: string; // CSS color, used by the corporate theme
  setTitle: (t: string) => void;
  setIconKey: (k: IconKey) => void;
  setTheme: (t: Theme) => void;
  setLayout: (l: Layout) => void;
  setCalendarMode: (m: CalendarMode) => void;
  setBrandColor: (c: string) => void;
}

const ssrSafeStorage = {
  getItem: (n: string) => {
    if (typeof window === "undefined") return null;
    try {
      return window.localStorage.getItem(n);
    } catch {
      return null;
    }
  },
  setItem: (n: string, v: string) => {
    if (typeof window === "undefined") return;
    try {
      window.localStorage.setItem(n, v);
    } catch {}
  },
  removeItem: (n: string) => {
    if (typeof window === "undefined") return;
    try {
      window.localStorage.removeItem(n);
    } catch {}
  },
};

export const useConfig = create<ConfigState>()(
  persist(
    (set) => ({
      title: "پنل کارگاه تولید و پخش",
      iconKey: "factory",
      theme: "modern",
      layout: "sidebar-right",
      calendarMode: "jalali",
      brandColor: "oklch(0.55 0.18 250)",
      setTitle: (title) => set({ title }),
      setIconKey: (iconKey) => set({ iconKey }),
      setTheme: (theme) => set({ theme }),
      setLayout: (layout) => set({ layout }),
      setCalendarMode: (calendarMode) => set({ calendarMode }),
      setBrandColor: (brandColor) => set({ brandColor }),
    }),
    {
      name: "workshop_config",
      storage: createJSONStorage(() => ssrSafeStorage),
      partialize: (s) => ({
        title: s.title,
        iconKey: s.iconKey,
        theme: s.theme,
        layout: s.layout,
        calendarMode: s.calendarMode,
        brandColor: s.brandColor,
      }),
    }
  )
);
