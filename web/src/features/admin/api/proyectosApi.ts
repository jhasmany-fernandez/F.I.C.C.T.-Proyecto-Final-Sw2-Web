/** Llamadas a la API de proyectos para el admin. Sprint 1 — PB-18. */

import { apiClient } from "@/shared/api/client";
import type {
  ProyectoListOut,
  ProyectoReasignarIn,
  ProyectosFilter,
  ProyectosPageOut,
} from "../types";

export async function listarProyectosOrg(
  page = 1,
  pageSize = 20,
  filtros?: ProyectosFilter,
): Promise<ProyectosPageOut> {
  const { data } = await apiClient.get<ProyectosPageOut>("/admin/proyectos", {
    params: {
      page,
      page_size: pageSize,
      ...filtros,
    },
  });
  return data;
}

export async function archivarProyectoAdmin(
  id: number,
): Promise<ProyectoListOut> {
  const { data } = await apiClient.patch<ProyectoListOut>(
    `/admin/proyectos/${id}/archivar`,
  );
  return data;
}

export async function reasignarTecnico(
  id: number,
  body: ProyectoReasignarIn,
): Promise<ProyectoListOut> {
  const { data } = await apiClient.patch<ProyectoListOut>(
    `/admin/proyectos/${id}/reasignar`,
    body,
  );
  return data;
}
