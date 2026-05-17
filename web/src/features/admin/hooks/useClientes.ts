/**
 * Hooks TanStack Query para gestión de clientes admin.
 * Sp1-35 — PB-19.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  actualizarCliente,
  crearCliente,
  desactivarCliente,
  listarTodosClientes,
} from "../api/clientesApi";
import type { ClienteCreate, ClienteUpdate } from "../types";

const CLIENTES_KEY = ["admin", "clientes"] as const;

async function refrescarClientes(queryClient: ReturnType<typeof useQueryClient>) {
  await queryClient.invalidateQueries({ queryKey: CLIENTES_KEY });
  await queryClient.refetchQueries({ queryKey: CLIENTES_KEY, type: "active" });
}

export function useClientes() {
  return useQuery({
    queryKey: CLIENTES_KEY,
    queryFn: listarTodosClientes,
  });
}

export function useCrearCliente() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (datos: ClienteCreate) => crearCliente(datos),
    onSuccess: async () => {
      await refrescarClientes(queryClient);
    },
  });
}

export function useActualizarCliente() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, datos }: { id: number; datos: ClienteUpdate }) =>
      actualizarCliente(id, datos),
    onSuccess: async () => {
      await refrescarClientes(queryClient);
    },
  });
}

export function useDesactivarCliente() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => desactivarCliente(id),
    onSuccess: async () => {
      await refrescarClientes(queryClient);
    },
  });
}
