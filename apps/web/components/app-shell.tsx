"use client";

import type { ReactNode } from "react";
import { usePathname } from "next/navigation";

import { Sidebar } from "@/components/sidebar";
import { StoreShell } from "@/components/store-shell";
import { Topbar } from "@/components/topbar";

type AppShellProps = {
  children: ReactNode;
};

export function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();

  if (pathname === "/settings") {
    return <StoreShell>{children}</StoreShell>;
  }

  if (pathname === "/login" || pathname === "/forgot-password") {
    return <div className="auth-shell">{children}</div>;
  }

  return (
    <div className="dashboard-app">
      <Sidebar />
      <div className="dashboard-main">
        <Topbar />
        <main className="dashboard-content">{children}</main>
      </div>
    </div>
  );
}
