"use client";

import { create } from "zustand";
import {
  api,
  setDistributorTokens,
  clearDistributorTokens,
  getDistributorTokens,
  clearTokens,
  ApiError,
} from "@/lib/api";
import type { MOCK_DISTRIBUTOR_USER } from "@/lib/mock-data";

export type DistributorUser = typeof MOCK_DISTRIBUTOR_USER;

interface DistributorAuthState {
  user: DistributorUser | null;
  status: "loading" | "authenticated" | "unauthenticated";
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  hydrate: () => Promise<void>;
}

/**
 * Auth store for the distributor mobile PWA. Kept completely separate from the
 * admin panel's auth-store so the two sessions don't interfere.
 *
 * Tokens are stored in localStorage under `dist_access` / `dist_refresh`. The
 * shared api.ts client prefers those keys over the admin's `workshop_*` keys,
 * so distributor requests automatically pick up the right JWT.
 */
export const useDistributorAuthStore = create<DistributorAuthState>((set) => ({
  user: null,
  status: "loading",

  login: async (username, password) => {
    const res = await api<{
      access: string;
      refresh: string;
      user?: DistributorUser;
    }>("/auth/login/", { method: "POST", body: { username, password } });

    // The endpoint should return a user with role='distributor'. If it doesn't,
    // reject the login.
    const user = res.user ?? null;
    if (user && user.role && user.role !== "distributor") {
      clearDistributorTokens();
      throw new ApiError(403, "این حساب کاربری به اپلیکیشن عامل پخش دسترسی ندارد.");
    }

    // Make sure admin tokens are cleared so the admin panel doesn't accidentally
    // treat the distributor as an admin user.
    clearTokens();
    setDistributorTokens(res.access, res.refresh);

    const fullUser =
      user ??
      (await api<DistributorUser>("/auth/me/"));

    if (fullUser.role && fullUser.role !== "distributor") {
      clearDistributorTokens();
      throw new ApiError(403, "این حساب کاربری به اپلیکیشن عامل پخش دسترسی ندارد.");
    }
    set({ user: fullUser, status: "authenticated" });
  },

  logout: async () => {
    try {
      await api("/auth/logout/", { method: "POST" });
    } catch {
      /* even if backend fails we still clear locally */
    }
    clearDistributorTokens();
    set({ user: null, status: "unauthenticated" });
  },

  hydrate: async () => {
    const { access } = getDistributorTokens();
    if (!access) {
      set({ status: "unauthenticated" });
      return;
    }
    try {
      const user = await api<DistributorUser>("/auth/me/");
      if (user.role && user.role !== "distributor") {
        // Not a distributor — refuse.
        clearDistributorTokens();
        set({ user: null, status: "unauthenticated" });
        return;
      }
      set({ user, status: "authenticated" });
    } catch {
      clearDistributorTokens();
      set({ user: null, status: "unauthenticated" });
    }
  },
}));
