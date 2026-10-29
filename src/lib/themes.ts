// Theme definitions for the three display themes: Modern (مدرن), Classic (کلاسیک), Corporate (شرکتی).
// Each theme controls primary/accent colors, border radius, and card style.
// Themes are applied to the document via `data-theme="<key>"` on a wrapper element;
// globals.css maps each attribute value to the corresponding CSS variables.

export type ThemeKey = "modern" | "classic" | "corporate";

export interface ThemeDef {
  name: string;          // Persian label
  description: string;   // helper text
  primary: string;       // CSS color (overrides --primary)
  accent: string;        // CSS color (overrides --accent)
  radius: string;        // CSS length (overrides --radius)
  cardStyle: "glass" | "flat" | "subtle-gradient";
  swatch: string;        // background for the picker dot
}

export const THEMES: Record<ThemeKey, ThemeDef> = {
  modern: {
    name: "مدرن",
    description: "رنگ سبز فیروزه‌ای، شیشه‌ای، گوشه‌های گرد",
    primary: "oklch(0.6 0.13 160)",          // emerald-ish
    accent: "oklch(0.94 0.04 160)",
    radius: "0.75rem",
    cardStyle: "glass",
    swatch: "linear-gradient(135deg, oklch(0.6 0.13 160), oklch(0.7 0.13 175))",
  },
  classic: {
    name: "کلاسیک",
    description: "آبی رسمی، گوشه‌های تیز، کارت مسطح",
    primary: "oklch(0.45 0.18 250)",          // royal blue
    accent: "oklch(0.3 0.04 250)",
    radius: "0.375rem",
    cardStyle: "flat",
    swatch: "linear-gradient(135deg, oklch(0.45 0.18 250), oklch(0.5 0.16 260))",
  },
  corporate: {
    name: "شرکتی",
    description: "رنگ سفارشی برند، گرادیان ملایم",
    primary: "var(--brand-color)",            // customizable via brandColor
    accent: "oklch(0.55 0.08 230)",
    radius: "0.5rem",
    cardStyle: "subtle-gradient",
    swatch: "linear-gradient(135deg, var(--brand-color), oklch(0.55 0.08 230))",
  },
};

export const THEME_LIST: Array<{ key: ThemeKey; def: ThemeDef }> = Object.entries(THEMES).map(
  ([key, def]) => ({ key: key as ThemeKey, def })
);
