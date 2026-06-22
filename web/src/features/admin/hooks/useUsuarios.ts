/**
 * Hook TanStack Query para gestión de usuarios admin.
 * Sp1-10 — PB-13.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  actualizarUsuario,
  crearUsuario,
  listarUsuarios,
} from "../api/usuariosApi";
import type { UsuarioCreate, UsuarioUpdate } from "../types";

export const USUARIOS_KEY = ["admin", "usuarios"] as const;

export function useUsuarios(soloActivos = false) {
  return useQuery({
    queryKey: [...USUARIOS_KEY, { soloActivos }],
    queryFn: () => listarUsuarios(soloActivos),
  });
}

export function useCrearUsuario() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (datos: UsuarioCreate) => crearUsuario(datos),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: USUARIOS_KEY });
    },
  });
}

export function useActualizarUsuario() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, datos }: { id: number; datos: UsuarioUpdate }) =>
      actualizarUsuario(id, datos),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: USUARIOS_KEY });
    },
  });
}
