/**
 * Hooks TanStack Query para proyectos de la organización (admin).
 * Sp1-26, Sp1-51, Sp1-52 — PB-18.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  archivarProyectoAdmin,
  listarProyectosOrg,
  reasignarTecnico,
} from "../api/proyectosApi";
import type { ProyectoReasignarIn, ProyectosFilter } from "../types";

export function useProyectosOrg(
  page = 1,
  pageSize = 20,
  filtros?: ProyectosFilter,
) {
  return useQuery({
    queryKey: ["admin", "proyectos", { page, pageSize, ...filtros }],
    queryFn: () => listarProyectosOrg(page, pageSize, filtros),
    placeholderData: (prev) => prev,
  });
}

export function useArchivarProyectoAdmin() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => archivarProyectoAdmin(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin", "proyectos"] }),
  });
}

export function useReasignarTecnico() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: number; body: ProyectoReasignarIn }) =>
      reasignarTecnico(id, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin", "proyectos"] }),
  });
}
