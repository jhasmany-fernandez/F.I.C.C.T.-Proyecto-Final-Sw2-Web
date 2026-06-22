/** Tipos TypeScript para el módulo admin. Sprint 1 — PB-13, PB-18, PB-19. */

export interface UsuarioOut {
  id: number;
  nombre: string;
  email: string;
  rol: "admin" | "tecnico";
  activo: boolean;
  created_at: string;
}

export interface UsuarioCreate {
  nombre: string;
  email: string;
  password: string;
  rol: "admin" | "tecnico";
}

export interface UsuarioUpdate {
  nombre?: string;
  email?: string;
  rol?: "admin" | "tecnico";
  activo?: boolean;
  password?: string;
}

export interface ClienteBasicoOut {
  id: number;
  nombre: string;
}

export interface ClienteOut {
  id: number;
  nombre: string;
  activo: boolean;
  created_at: string;
}

export interface ClienteCreate {
  nombre: string;
}

export interface ClienteUpdate {
  nombre?: string;
  activo?: boolean;
}

export interface TecnicoBasicoOut {
  id: number;
  nombre: string;
  email: string;
}

export interface ProyectoListOut {
  id: number;
  nombre: string;
  descripcion: string | null;
  cliente: ClienteBasicoOut | null;
  estado: "nuevo" | "en_progreso" | "completado" | "archivado";
  ultima_actividad: string;
  cantidad_puntos: number;
  tecnico: TecnicoBasicoOut;
  created_at: string;
}

export interface ProyectosPageOut {
  items: ProyectoListOut[];
  total: number;
  page: number;
  page_size: number;
}

export interface ProyectosFilter {
  tecnico_id?: number;
  estado?: string;
  fecha_desde?: string;
  fecha_hasta?: string;
}

export interface ProyectoReasignarIn {
  tecnico_id: number;
}

export interface ProyectoAdminCreate {
  nombre: string;
  descripcion?: string | null;
  cliente_id?: number | null;
  tecnico_id: number;
  estado: "nuevo" | "en_progreso" | "completado" | "archivado";
}

export type ProyectoAdminUpdate = Partial<ProyectoAdminCreate>;

export interface PlanoOut {
  id: number;
  proyecto_id: number;
  nombre: string;
  formato: "png" | "jpg" | "pdf";
  ancho_px: number;
  alto_px: number;
  tamano_bytes: number;
  url_firmada: string;
  calibrado: boolean;
  cantidad_puntos: number;
  escala_m_por_px: number | null;
  distancia_real_m: number | null;
  created_at: string;
  updated_at: string;
}

export interface APDisponibleOut {
  bssid: string;
  ssid: string;
  canal: number | null;
  frecuencia_mhz: number | null;
  rssi_promedio: number;
  pos_x: number;
  pos_y: number;
  cantidad_puntos: number;
  seleccionado: boolean;
}

export type EstadoGobernanzaConjunto =
  | "borrador_tecnico"
  | "preliminar"
  | "pendiente_revision"
  | "aprobado_interno"
  | "publicado_cliente"
  | "descartado";

export interface ConjuntoAPItemOut {
  bssid: string;
  ssid: string;
  canal: number | null;
  frecuencia_mhz: number | null;
  rssi_promedio: number | null;
  pos_x: number | null;
  pos_y: number | null;
  cantidad_puntos: number | null;
}

export interface ConjuntoAPOut {
  id: number;
  plano_id: number;
  nombre: string;
  proposito: string;
  descripcion: string | null;
  es_principal: boolean;
  origen: "manual_movil" | "manual_web" | "ia" | string;
  estado_gobernanza: EstadoGobernanzaConjunto | string;
  creado_por_id: number | null;
  cantidad_aps: number;
  items: ConjuntoAPItemOut[];
  created_at: string;
  updated_at: string;
}

export interface FuenteEntradaEscenarioIn {
  tipo:
    | "SELECCION_APS_MAPA"
    | "INVENTARIO_RF"
    | "BASELINE_OBSERVADO"
    | "CONJUNTO_EXISTENTE";
  nombre?: string;
  proposito?: string;
  ap_ids: number[];
  bssids?: string[];
  conjunto_id?: number | null;
}

export interface RecomendacionAPOut {
  id: number;
  orden: number;
  accion: string;
  coord_x: number;
  coord_y: number;
  altura_m: number;
  tipo_montaje: string;
  banda: string;
  modelo_ap: string;
  costo_estimado: number;
  rssi_proyectado: number;
  radios: Array<Record<string, unknown>>;
  justificacion: string;
}

export interface EscenarioOptimizadoOut {
  id: number;
  proyecto_id: number;
  plano_id: number;
  mapa_actual_id: number | null;
  mapa_proyectado_id: number | null;
  conjunto_base_id: number | null;
  origen: string;
  estado_gobernanza:
    | "pendiente_revision"
    | "aprobado_interno"
    | "publicado_cliente"
    | "descartado"
    | string;
  generado_por_id: number | null;
  aprobado_por_id: number | null;
  publicado_por_id: number | null;
  aprobado_at: string | null;
  publicado_at: string | null;
  nombre: string;
  tipo_negocio: string;
  perfil: string;
  politica_combinacion: string;
  banda: string;
  bandas: string[];
  modelo_ap: string;
  pct_cobertura_actual: number;
  pct_cobertura: number;
  costo_estimado: number;
  cantidad_aps: number;
  resumen: string;
  restricciones: Record<string, unknown>;
  metricas: Record<string, unknown>;
  mapas_por_banda: Record<string, unknown>;
  mapas_actuales_por_banda: Record<string, unknown>;
  supuestos: string[];
  confianza: string;
  version_motor: string;
  recomendaciones: RecomendacionAPOut[];
  created_at: string;
}

export interface RestriccionesEscenarioIn {
  plano_id?: number;
  fuente_entrada?: FuenteEntradaEscenarioIn;
  max_aps: number;
  bandas: Array<"2.4" | "5">;
  umbral_objetivo_dbm: number;
  resolucion: number;
}

export interface EscenariosGeneradosOut {
  escenarios: EscenarioOptimizadoOut[];
}

export type EstadoGobernanzaEscenario =
  | "pendiente_revision"
  | "aprobado_interno"
  | "publicado_cliente"
  | "descartado";

export interface ContenidoEnlaceIn {
  conjunto_ids?: number[];
  mapa_ids?: number[];
  analisis_ids?: number[];
  escenario_ids?: number[];
  reporte_id?: number | null;
}

export interface EnlaceClienteOut {
  id: number;
  proyecto_id: number;
  url_publica: string;
  expira_en: string;
  revocado: boolean;
  accesos: number;
  ultimo_acceso: string | null;
  ip_ultimo_acceso: string | null;
  contenido: Required<ContenidoEnlaceIn>;
  created_at: string;
}

export interface PortalProyectoOut {
  id: number;
  nombre: string;
  cliente: string | null;
  descripcion: string | null;
}

export interface AnalisisCoberturaOut {
  id: number;
  mapa_calor_id: number;
  pct_cobertura: number;
  pct_zonas_muertas: number;
  celdas_zonas_muertas: number;
  cantidad_solapamientos: number;
  cantidad_interferencias: number;
  hallazgos: Record<string, unknown>;
  resumen: string;
  aps_detectados: Array<{
    id: number;
    bssid: string;
    ssid: string;
    canal: number | null;
    frecuencia_mhz: number | null;
    rssi_promedio: number;
    pos_x: number;
    pos_y: number;
    confirmado: boolean;
    created_at: string;
  }>;
  created_at: string;
}

export interface MapaCalorPortalOut {
  id: number;
  plano_id: number;
  conjunto_ap_id: number | null;
  analisis_id: number | null;
  modo_generacion: string;
  algoritmo: string;
  resolucion: number;
  bssid: string;
  ssid: string;
  ap_pos_x: number;
  ap_pos_y: number;
  aps_interes: APDisponibleOut[];
  bssids_generacion: string[];
  url_imagen: string;
  matriz: number[][];
  escala: Array<{ desde: number; hasta: number; color: string; etiqueta: string }>;
  cantidad_puntos: number;
  rssi_min: number;
  rssi_max: number;
  rssi_promedio: number;
  puntos_lectura: Array<{ punto_id: number; pos_x: number; pos_y: number; rssi: number }>;
  advertencias: string[];
  created_at: string;
}

export type MapaCalorOut = MapaCalorPortalOut;

export interface ComparacionEscenarioOut {
  escenario: EscenarioOptimizadoOut;
  heatmap_actual: MapaCalorOut;
  heatmap_proyectado: MapaCalorOut;
  matriz_diferencia: number[][];
  comparacion_por_banda: Record<string, unknown>;
  resumen: {
    delta_pct_cobertura: number;
    delta_zonas_muertas: number;
    costo_estimado: number;
    cantidad_cambios: number;
    lectura: string;
  };
}

export interface ReporteOut {
  id: number;
  proyecto_id: number;
  escenario_id: number | null;
  estado: string;
  url_descarga: string | null;
  sha256: string | null;
  tamanio_bytes: number;
  error: string | null;
  created_at: string;
  updated_at: string;
}

export interface PortalClienteOut {
  proyecto: PortalProyectoOut;
  planos: PlanoOut[];
  conjuntos: ConjuntoAPOut[];
  heatmaps: MapaCalorPortalOut[];
  analisis: AnalisisCoberturaOut[];
  escenarios: EscenarioOptimizadoOut[];
  reporte_disponible: boolean;
}
