"use client";

import { create } from "zustand";
import { api, setTokens, clearTokens, getTokens } from "@/lib/api";
import type { MOCK_USER } from "@/lib/mock-data";

export type AuthUser = typeof MOCK_USER;

interface AuthState {
  user: AuthUser | null;
  status: "loading" | "authenticated" | "unauthenticated";
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  hydrate: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  status: "loading",

  login: async (username, password) => {
    const res = await api<{ access: string; refresh: string; user?: AuthUser }>(
      "/auth/login/",
      { method: "POST", body: { username, password } }
    );
    setTokens(res.access, res.refresh);
    const user = res.user ?? (await api<AuthUser>("/auth/me/"));
    set({ user, status: "authenticated" });
  },

  logout: async () => {
    try {
      await api("/auth/logout/", { method: "POST" });
    } catch {
      /* even if backend fails we still clear locally */
    }
    clearTokens();
    set({ user: null, status: "unauthenticated" });
  },

  hydrate: async () => {
    const { access } = getTokens();
    if (!access) {
      set({ status: "unauthenticated" });
      return;
    }
    try {
      const user = await api<AuthUser>("/auth/me/");
      set({ user, status: "authenticated" });
    } catch {
      clearTokens();
      set({ status: "unauthenticated" });
    }
  },
}));
