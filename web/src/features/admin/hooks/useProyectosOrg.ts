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

const PROYECTOS_KEY = ["admin", "proyectos"] as const;

async function refrescarProyectos(qc: ReturnType<typeof useQueryClient>) {
  await qc.invalidateQueries({ queryKey: PROYECTOS_KEY });
  await qc.refetchQueries({ queryKey: PROYECTOS_KEY, type: "active" });
}

export function useProyectosOrg(
  page = 1,
  pageSize = 20,
  filtros?: ProyectosFilter,
) {
  return useQuery({
    queryKey: [...PROYECTOS_KEY, { page, pageSize, ...filtros }],
    queryFn: () => listarProyectosOrg(page, pageSize, filtros),
    placeholderData: (prev) => prev,
  });
}

export function useArchivarProyectoAdmin() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => archivarProyectoAdmin(id),
    onSuccess: async () => {
      await refrescarProyectos(qc);
    },
  });
}

export function useReasignarTecnico() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: number; body: ProyectoReasignarIn }) =>
      reasignarTecnico(id, body),
    onSuccess: async () => {
      await refrescarProyectos(qc);
    },
  });
}
