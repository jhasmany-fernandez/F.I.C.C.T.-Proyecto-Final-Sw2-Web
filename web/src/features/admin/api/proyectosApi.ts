/** Llamadas a la API de proyectos para el admin. Sprint 1 — PB-18. */

import { apiClient } from "@/shared/api/client";
import type {
  APDisponibleOut,
  AnalisisCoberturaOut,
  ComparacionEscenarioOut,
  ContenidoEnlaceIn,
  ConjuntoAPOut,
  EnlaceClienteOut,
  EscenarioOptimizadoOut,
  EscenariosGeneradosOut,
  EstadoGobernanzaConjunto,
  EstadoGobernanzaEscenario,
  MapaCalorOut,
  PlanoOut,
  ProyectoListOut,
  ProyectoAdminCreate,
  ProyectoAdminUpdate,
  ProyectoReasignarIn,
  ProyectosFilter,
  ProyectosPageOut,
  RestriccionesEscenarioIn,
  ReporteOut,
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

export async function crearProyectoAdmin(
  body: ProyectoAdminCreate,
): Promise<ProyectoListOut> {
  const { data } = await apiClient.post<ProyectoListOut>(
    "/admin/proyectos",
    body,
  );
  return data;
}

export async function actualizarProyectoAdmin(
  id: number,
  body: ProyectoAdminUpdate,
): Promise<ProyectoListOut> {
  const { data } = await apiClient.put<ProyectoListOut>(
    `/admin/proyectos/${id}`,
    body,
  );
  return data;
}

export async function eliminarProyectoAdmin(id: number): Promise<void> {
  await apiClient.delete(`/admin/proyectos/${id}`);
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

export async function listarPlanosProyecto(
  proyectoId: number,
): Promise<PlanoOut[]> {
  const { data } = await apiClient.get<PlanoOut[]>(
    `/proyectos/${proyectoId}/planos`,
  );
  return data;
}

export async function listarAPsPlano(
  planoId: number,
): Promise<APDisponibleOut[]> {
  const { data } = await apiClient.get<APDisponibleOut[]>(
    `/planos/${planoId}/aps`,
  );
  return data;
}

export async function listarConjuntosPlano(
  planoId: number,
): Promise<ConjuntoAPOut[]> {
  const { data } = await apiClient.get<ConjuntoAPOut[]>(
    `/planos/${planoId}/conjuntos-ap`,
  );
  return data;
}

export async function listarMapasPlano(planoId: number): Promise<MapaCalorOut[]> {
  const { data } = await apiClient.get<MapaCalorOut[]>(`/planos/${planoId}/mapas`);
  return data;
}

export async function crearConjuntoAP(
  planoId: number,
  body: {
    nombre: string;
    proposito: string;
    descripcion?: string | null;
    es_principal?: boolean;
    bssids: string[];
  },
): Promise<ConjuntoAPOut> {
  const { data } = await apiClient.post<ConjuntoAPOut>(
    `/planos/${planoId}/conjuntos-ap`,
    body,
  );
  return data;
}

export async function actualizarConjuntoAP(
  conjuntoId: number,
  body: Partial<{
    nombre: string;
    proposito: string;
    descripcion: string | null;
    es_principal: boolean;
    bssids: string[];
  }>,
): Promise<ConjuntoAPOut> {
  const { data } = await apiClient.patch<ConjuntoAPOut>(
    `/conjuntos-ap/${conjuntoId}`,
    body,
  );
  return data;
}

export async function generarHeatmapConjunto(
  conjuntoId: number,
  body: {
    modo: "INDIVIDUAL" | "SUBCONJUNTO" | "CONJUNTO_COMPLETO";
    bssids?: string[];
    algoritmo: "IDW" | "KRIGING";
    resolucion: 64 | 128 | 256;
  },
): Promise<MapaCalorOut> {
  const { data } = await apiClient.post<MapaCalorOut>(
    `/conjuntos-ap/${conjuntoId}/heatmaps`,
    body,
  );
  return data;
}

export async function analizarMapa(mapaId: number): Promise<AnalisisCoberturaOut> {
  const { data } = await apiClient.post<AnalisisCoberturaOut>(
    `/mapas/${mapaId}/analisis`,
  );
  return data;
}

export async function cambiarEstadoConjuntoAP(
  conjuntoId: number,
  estadoGobernanza: EstadoGobernanzaConjunto,
): Promise<ConjuntoAPOut> {
  const { data } = await apiClient.patch<ConjuntoAPOut>(
    `/conjuntos-ap/${conjuntoId}`,
    { estado_gobernanza: estadoGobernanza },
  );
  return data;
}

export async function listarEscenariosProyecto(
  proyectoId: number,
): Promise<EscenarioOptimizadoOut[]> {
  const { data } = await apiClient.get<EscenarioOptimizadoOut[]>(
    `/proyectos/${proyectoId}/escenarios`,
  );
  return data;
}

export async function generarEscenariosProyecto(
  proyectoId: number,
  body: RestriccionesEscenarioIn,
): Promise<EscenariosGeneradosOut> {
  const { data } = await apiClient.post<EscenariosGeneradosOut>(
    `/proyectos/${proyectoId}/escenarios`,
    body,
  );
  return data;
}

export async function cambiarEstadoEscenario(
  escenarioId: number,
  estadoGobernanza: EstadoGobernanzaEscenario,
): Promise<EscenarioOptimizadoOut> {
  const { data } = await apiClient.patch<EscenarioOptimizadoOut>(
    `/escenarios/${escenarioId}/estado`,
    { estado_gobernanza: estadoGobernanza },
  );
  return data;
}

export async function compararEscenario(
  escenarioId: number,
): Promise<ComparacionEscenarioOut> {
  const { data } = await apiClient.get<ComparacionEscenarioOut>(
    `/escenarios/${escenarioId}/comparacion`,
  );
  return data;
}

export async function listarReportesProyecto(
  proyectoId: number,
): Promise<ReporteOut[]> {
  const { data } = await apiClient.get<ReporteOut[]>(
    `/proyectos/${proyectoId}/reportes`,
  );
  return data;
}

export async function eliminarEscenario(escenarioId: number): Promise<void> {
  await apiClient.delete(`/escenarios/${escenarioId}`);
}

export async function eliminarEscenariosProyecto(
  proyectoId: number,
): Promise<{ eliminados: number }> {
  const { data } = await apiClient.delete<{ eliminados: number }>(
    `/proyectos/${proyectoId}/escenarios`,
  );
  return data;
}

export async function listarEnlacesCliente(
  proyectoId: number,
): Promise<EnlaceClienteOut[]> {
  const { data } = await apiClient.get<EnlaceClienteOut[]>(
    `/share/proyectos/${proyectoId}/enlaces`,
  );
  return data;
}

export async function crearEnlaceCliente(
  proyectoId: number,
  body: { expira_en_dias: number; contenido: ContenidoEnlaceIn },
): Promise<EnlaceClienteOut> {
  const { data } = await apiClient.post<EnlaceClienteOut>(
    `/share/proyectos/${proyectoId}/enlaces`,
    body,
  );
  return data;
}

export async function actualizarEnlaceCliente(
  enlaceId: number,
  revocado: boolean,
): Promise<EnlaceClienteOut> {
  const { data } = await apiClient.patch<EnlaceClienteOut>(
    `/share/enlaces/${enlaceId}`,
    { revocado },
  );
  return data;
}
