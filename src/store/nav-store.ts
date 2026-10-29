"use client";

import { create } from "zustand";

export type ViewKey =
  | "dashboard"
  | "products"
  | "purchase"
  | "workshop_issue"
  | "production"
  | "product_output"
  | "sales"
  | "inventory"
  | "accounting"
  | "dispatch_transfers"
  | "distribution"
  | "reports"
  | "settings";

interface NavState {
  view: ViewKey;
  setView: (v: ViewKey) => void;
}

export const useNavStore = create<NavState>((set) => ({
  view: "dashboard",
  setView: (view) => set({ view }),
}));
