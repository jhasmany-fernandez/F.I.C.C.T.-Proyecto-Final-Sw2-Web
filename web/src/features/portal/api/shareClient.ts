import axios from "axios";
import type { PortalClienteOut } from "@/features/admin/types";

const portalClient = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

export async function obtenerPortalCliente(
  token: string,
): Promise<PortalClienteOut> {
  const { data } = await portalClient.get<PortalClienteOut>(`/share/${token}`);
  return data;
}

export function urlReportePortal(token: string): string {
  return `/api/share/${token}/reporte`;
}
