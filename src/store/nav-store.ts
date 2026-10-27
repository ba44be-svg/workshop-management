"use client";

import { create } from "zustand";

export type ViewKey =
  | "dashboard"
  | "products"
  | "purchase"
  | "workshop_issue"
  | "production"
  | "product_output"
  | "finished_goods"
  | "sales"
  | "inventory"
  | "accounting"
  | "dispatch_transfers"
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
