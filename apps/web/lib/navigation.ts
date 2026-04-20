import type { IconName } from "@/components/icons";

export type NavItem = {
  label: string;
  href: string;
  icon: IconName;
  description: string;
};

export const navigationItems: NavItem[] = [
  {
    label: "Store",
    href: "/settings",
    icon: "store",
    description: "Portada e-commerce",
  },
  {
    label: "Dashboard",
    href: "/dashboard",
    icon: "dashboard",
    description: "Resumen operativo",
  },
  {
    label: "Planos",
    href: "/floor-plans",
    icon: "plans",
    description: "Ambientes y niveles",
  },
  {
    label: "Mediciones",
    href: "/measurements",
    icon: "measurements",
    description: "Puntos y lecturas",
  },
  {
    label: "Escaneos",
    href: "/scans",
    icon: "wifi",
    description: "Redes detectadas",
  },
  {
    label: "Reportes",
    href: "/reports",
    icon: "reports",
    description: "Cobertura e insights",
  },
];
