// نسخه‌ی production از api.ts
// این فایل برای محیط آنلاین استفاده می‌شود

const PROD_API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export function resolveBaseUrl(): string {
  if (typeof window === "undefined") {
    // در server-side (SSR)
    return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
  }
  // در client-side
  return process.env.NEXT_PUBLIC_API_URL || `http://${window.location.hostname}:8000/api`;
}

export const BASE_URL = resolveBaseUrl();
