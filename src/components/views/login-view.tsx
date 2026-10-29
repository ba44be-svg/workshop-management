"use client";

import * as React from "react";
import { motion } from "framer-motion";
import { Factory, Loader2, Lock, User } from "lucide-react";
import { toast } from "sonner";
import { useAuthStore } from "@/store/auth-store";
import { useConfig, ICON_MAP } from "@/store/config-store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export function LoginView() {
  const { login } = useAuthStore();
  const { title, iconKey } = useConfig();
  const Icon = ICON_MAP[iconKey] ?? Factory;
  const [username, setUsername] = React.useState("admin");
  const [password, setPassword] = React.useState("Admin@12345678");
  const [loading, setLoading] = React.useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) {
      toast.error("نام کاربری و گذرواژه را وارد کنید.");
      return;
    }
    setLoading(true);
    try {
      await login(username, password);
      toast.success("ورود موفقیت‌آمیز بود. خوش آمدید!");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "خطا در ورود.";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-gradient-to-br from-accent/40 via-background to-accent/30 p-4">
      <div
        className="pointer-events-none absolute -top-24 -right-24 h-72 w-72 rounded-full bg-primary/10 blur-3xl"
        aria-hidden
      />
      <div
        className="pointer-events-none absolute -bottom-24 -left-24 h-72 w-72 rounded-full bg-chart-2/10 blur-3xl"
        aria-hidden
      />
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="relative w-full max-w-md"
      >
        <Card className="border-border/60 shadow-xl">
          <CardHeader className="text-center space-y-3">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-lg">
              <Icon className="h-7 w-7" />
            </div>
            <div className="space-y-1">
              <CardTitle className="text-xl">{title}</CardTitle>
              <CardDescription>برای ورود اطلاعات حساب خود را وارد کنید.</CardDescription>
            </div>
          </CardHeader>
          <CardContent>
            <form onSubmit={onSubmit} className="space-y-4" autoComplete="off">
              <div className="space-y-2">
                <Label htmlFor="username">نام کاربری</Label>
                <div className="relative">
                  <User className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    id="username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="pr-9"
                    placeholder="admin"
                    autoComplete="username"
                    dir="ltr"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">گذرواژه</Label>
                <div className="relative">
                  <Lock className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="pr-9"
                    placeholder="••••••••"
                    autoComplete="current-password"
                    dir="ltr"
                  />
                </div>
              </div>
              <Button type="submit" disabled={loading} className="w-full" size="lg">
                {loading && <Loader2 className="h-4 w-4 animate-spin" />}
                {loading ? "در حال ورود…" : "ورود"}
              </Button>
              <div className="rounded-lg border border-dashed bg-muted/40 px-3 py-2 text-center text-[11px] text-muted-foreground">
                کاربر تستی:{" "}
                <span className="font-mono nums" dir="ltr">admin / Admin@12345678</span>
              </div>
            </form>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
