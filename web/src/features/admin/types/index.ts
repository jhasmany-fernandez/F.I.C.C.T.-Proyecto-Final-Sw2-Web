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
