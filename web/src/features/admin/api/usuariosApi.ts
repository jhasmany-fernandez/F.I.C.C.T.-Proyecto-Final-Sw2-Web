/** Llamadas a la API de gestión de usuarios. Sprint 1 — PB-13. */

import { apiClient } from "@/shared/api/client";
import type { UsuarioCreate, UsuarioOut, UsuarioUpdate } from "../types";

export async function listarUsuarios(soloActivos = false): Promise<UsuarioOut[]> {
  const { data } = await apiClient.get<UsuarioOut[]>("/admin/usuarios", {
    params: soloActivos ? { solo_activos: true } : undefined,
  });
  return data;
}

export async function crearUsuario(datos: UsuarioCreate): Promise<UsuarioOut> {
  const { data } = await apiClient.post<UsuarioOut>("/admin/usuarios", datos);
  return data;
}

export async function actualizarUsuario(
  id: number,
  datos: UsuarioUpdate
): Promise<UsuarioOut> {
  const { data } = await apiClient.patch<UsuarioOut>(
    `/admin/usuarios/${id}`,
    datos
  );
  return data;
}
