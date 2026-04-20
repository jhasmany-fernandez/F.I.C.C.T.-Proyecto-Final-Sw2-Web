import type { Metadata } from "next";
import type { ReactNode } from "react";

import { AppShell } from "@/components/app-shell";

import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "WiFiScope",
    template: "%s | WiFiScope",
  },
  description:
    "Frontend en Next.js con portada e-commerce y panel operativo para WiFiScope.",
  icons: {
    icon: "/wifiscope-app-icon.png",
    apple: "/wifiscope-app-icon.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <html lang="es" suppressHydrationWarning>
      <body>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
