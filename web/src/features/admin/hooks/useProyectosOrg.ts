/**
 * Hooks TanStack Query para proyectos de la organización (admin).
 * Sp1-26, Sp1-51, Sp1-52 — PB-18.
 */

import {
  useMutation,
  useQueries,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import {
  archivarProyectoAdmin,
  actualizarProyectoAdmin,
  actualizarEnlaceCliente,
  actualizarConjuntoAP,
  analizarMapa,
  cambiarEstadoConjuntoAP,
  cambiarEstadoEscenario,
  crearEnlaceCliente,
  crearProyectoAdmin,
  crearConjuntoAP,
  compararEscenario,
  eliminarEscenario,
  eliminarEscenariosProyecto,
  eliminarProyectoAdmin,
  generarEscenariosProyecto,
  generarHeatmapConjunto,
  listarConjuntosPlano,
  listarEnlacesCliente,
  listarMapasPlano,
  listarAPsPlano,
  listarEscenariosProyecto,
  listarPlanosProyecto,
  listarReportesProyecto,
  listarProyectosOrg,
  reasignarTecnico,
} from "../api/proyectosApi";
import type {
  ContenidoEnlaceIn,
  EstadoGobernanzaConjunto,
  EstadoGobernanzaEscenario,
  ProyectoReasignarIn,
  ProyectoAdminCreate,
  ProyectoAdminUpdate,
  ProyectosFilter,
  RestriccionesEscenarioIn,
} from "../types";

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

export function useCrearProyectoAdmin() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: ProyectoAdminCreate) => crearProyectoAdmin(body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin", "proyectos"] }),
  });
}

export function useActualizarProyectoAdmin() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: number; body: ProyectoAdminUpdate }) =>
      actualizarProyectoAdmin(id, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin", "proyectos"] }),
  });
}

export function useEliminarProyectoAdmin() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => eliminarProyectoAdmin(id),
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

export function usePlanosProyecto(proyectoId: number) {
  return useQuery({
    queryKey: ["admin", "proyectos", proyectoId, "planos"],
    queryFn: () => listarPlanosProyecto(proyectoId),
    enabled: proyectoId > 0,
  });
}

export function useAPsPlano(planoId: number | null) {
  return useQuery({
    queryKey: ["admin", "planos", planoId, "aps"],
    queryFn: () => listarAPsPlano(planoId ?? 0),
    enabled: typeof planoId === "number" && planoId > 0,
  });
}

export function useConjuntosPorPlanos(planoIds: number[]) {
  return useQueries({
    queries: planoIds.map((planoId) => ({
      queryKey: ["admin", "planos", planoId, "conjuntos-ap"],
      queryFn: () => listarConjuntosPlano(planoId),
      enabled: planoId > 0,
    })),
  });
}

export function useMapasPorPlanos(planoIds: number[]) {
  return useQueries({
    queries: planoIds.map((planoId) => ({
      queryKey: ["admin", "planos", planoId, "mapas"],
      queryFn: () => listarMapasPlano(planoId),
      enabled: planoId > 0,
    })),
  });
}

export function useCrearConjuntoAP() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ planoId, body }: { planoId: number; body: Parameters<typeof crearConjuntoAP>[1] }) =>
      crearConjuntoAP(planoId, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin", "planos"] }),
  });
}

export function useActualizarConjuntoAP() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ conjuntoId, body }: { conjuntoId: number; body: Parameters<typeof actualizarConjuntoAP>[1] }) =>
      actualizarConjuntoAP(conjuntoId, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin", "planos"] }),
  });
}

export function useGenerarHeatmapConjunto() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ conjuntoId, body }: { conjuntoId: number; body: Parameters<typeof generarHeatmapConjunto>[1] }) =>
      generarHeatmapConjunto(conjuntoId, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin", "planos"] }),
  });
}

export function useAnalizarMapa() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (mapaId: number) => analizarMapa(mapaId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin", "planos"] }),
  });
}

export function useCambiarEstadoConjuntoAP(proyectoId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      conjuntoId,
      estadoGobernanza,
    }: {
      conjuntoId: number;
      estadoGobernanza: EstadoGobernanzaConjunto;
    }) => cambiarEstadoConjuntoAP(conjuntoId, estadoGobernanza),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin", "planos"] });
      qc.invalidateQueries({
        queryKey: ["admin", "proyectos", proyectoId, "enlaces-cliente"],
      });
    },
  });
}

export function useEscenariosProyecto(proyectoId: number) {
  return useQuery({
    queryKey: ["admin", "proyectos", proyectoId, "escenarios"],
    queryFn: () => listarEscenariosProyecto(proyectoId),
    enabled: proyectoId > 0,
  });
}

export function useGenerarEscenariosProyecto(proyectoId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: RestriccionesEscenarioIn) =>
      generarEscenariosProyecto(proyectoId, body),
    onSuccess: () =>
      qc.invalidateQueries({
        queryKey: ["admin", "proyectos", proyectoId, "escenarios"],
      }),
  });
}

export function useCambiarEstadoEscenario(proyectoId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      escenarioId,
      estadoGobernanza,
    }: {
      escenarioId: number;
      estadoGobernanza: EstadoGobernanzaEscenario;
    }) => cambiarEstadoEscenario(escenarioId, estadoGobernanza),
    onSuccess: () =>
      qc.invalidateQueries({
        queryKey: ["admin", "proyectos", proyectoId, "escenarios"],
      }),
  });
}

export function useComparacionEscenario(escenarioId: number | null) {
  return useQuery({
    queryKey: ["admin", "escenarios", escenarioId, "comparacion"],
    queryFn: () => compararEscenario(escenarioId ?? 0),
    enabled: typeof escenarioId === "number" && escenarioId > 0,
  });
}

export function useReportesProyecto(proyectoId: number) {
  return useQuery({
    queryKey: ["admin", "proyectos", proyectoId, "reportes"],
    queryFn: () => listarReportesProyecto(proyectoId),
    enabled: proyectoId > 0,
  });
}

export function useEliminarEscenario(proyectoId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (escenarioId: number) => eliminarEscenario(escenarioId),
    onSuccess: () =>
      qc.invalidateQueries({
        queryKey: ["admin", "proyectos", proyectoId, "escenarios"],
      }),
  });
}

export function useEliminarEscenariosProyecto(proyectoId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => eliminarEscenariosProyecto(proyectoId),
    onSuccess: () =>
      qc.invalidateQueries({
        queryKey: ["admin", "proyectos", proyectoId, "escenarios"],
      }),
  });
}

export function useEnlacesCliente(proyectoId: number) {
  return useQuery({
    queryKey: ["admin", "proyectos", proyectoId, "enlaces-cliente"],
    queryFn: () => listarEnlacesCliente(proyectoId),
    enabled: proyectoId > 0,
  });
}

export function useCrearEnlaceCliente(proyectoId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: {
      expira_en_dias: number;
      contenido: ContenidoEnlaceIn;
    }) => crearEnlaceCliente(proyectoId, body),
    onSuccess: () =>
      qc.invalidateQueries({
        queryKey: ["admin", "proyectos", proyectoId, "enlaces-cliente"],
      }),
  });
}

export function useActualizarEnlaceCliente(proyectoId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      enlaceId,
      revocado,
    }: {
      enlaceId: number;
      revocado: boolean;
    }) => actualizarEnlaceCliente(enlaceId, revocado),
    onSuccess: () =>
      qc.invalidateQueries({
        queryKey: ["admin", "proyectos", proyectoId, "enlaces-cliente"],
      }),
  });
}
