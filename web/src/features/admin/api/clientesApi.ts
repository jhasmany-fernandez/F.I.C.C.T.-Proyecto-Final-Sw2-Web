/** Llamadas a la API de gestión de clientes. Sprint 1 — PB-19. */

import { apiClient } from "@/shared/api/client";
import type { ClienteCreate, ClienteOut, ClienteUpdate } from "../types";

export async function listarClientesActivos(): Promise<ClienteOut[]> {
  const { data } = await apiClient.get<ClienteOut[]>("/clientes");
  return data;
}

export async function listarTodosClientes(): Promise<ClienteOut[]> {
  const { data } = await apiClient.get<ClienteOut[]>("/admin/clientes");
  return data;
}

export async function crearCliente(datos: ClienteCreate): Promise<ClienteOut> {
  const { data } = await apiClient.post<ClienteOut>("/admin/clientes", datos);
  return data;
}

export async function actualizarCliente(
  id: number,
  datos: ClienteUpdate
): Promise<ClienteOut> {
  const { data } = await apiClient.put<ClienteOut>(
    `/admin/clientes/${id}`,
    datos
  );
  return data;
}

export async function desactivarCliente(id: number): Promise<ClienteOut> {
  const { data } = await apiClient.patch<ClienteOut>(
    `/admin/clientes/${id}/desactivar`
  );
  return data;
}
