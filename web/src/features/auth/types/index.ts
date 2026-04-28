/** Tipos TypeScript para el módulo de autenticación. Sprint 1 — PB-09. */

export interface UsuarioOut {
  id: number;
  nombre: string;
  email: string;
  rol: "admin" | "tecnico";
  activo: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  usuario: UsuarioOut;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface AuthState {
  usuario: UsuarioOut | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}
