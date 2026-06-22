/**
 * Hook de autenticación admin (Zustand).
 * Sp1-08 — PB-09 / PB-13.
 */

import { create } from "zustand";
import { login as apiLogin, logout as apiLogout } from "../api/authApi";
import type { AuthState, UsuarioOut } from "../types";
import {
  STORAGE_REFRESH,
  STORAGE_USER,
  guardarUltimoEmail,
  guardarUsuario,
  haySesionGuardada,
  limpiarSesion,
  obtenerToken,
  obtenerUsuarioGuardado,
} from "@/shared/api/authStorage";

interface AuthStore extends AuthState {
  iniciarSesion: (
    email: string,
    password: string,
    recordar: boolean,
  ) => Promise<void>;
  cerrarSesion: () => Promise<void>;
}

/**
 * Lee la sesión guardada en localStorage de forma síncrona.
 * Se ejecuta al crear el store para que el primer render ya conozca
 * el estado real de autenticación (evita pantallas en blanco que
 * solo se corrigen recargando la página).
 */
function sesionInicial(): Pick<AuthState, "usuario" | "isAuthenticated"> {
  const raw = obtenerUsuarioGuardado();
  const tieneToken = haySesionGuardada();

  if (raw && tieneToken) {
    try {
      return { usuario: JSON.parse(raw) as UsuarioOut, isAuthenticated: true };
    } catch {
      limpiarSesion();
    }
  } else if (raw && !tieneToken) {
    // Sesión inconsistente: hay perfil guardado pero los tokens expiraron o
    // fueron eliminados. Limpiar para evitar el bucle login ↔ usuarios.
    localStorage.removeItem(STORAGE_USER);
    sessionStorage.removeItem(STORAGE_USER);
  }

  return { usuario: null, isAuthenticated: false };
}

export const useAuth = create<AuthStore>((set) => ({
  ...sesionInicial(),
  isLoading: false,
  error: null,

  iniciarSesion: async (email, password, recordar) => {
    set({ isLoading: true, error: null });
    try {
      const data = await apiLogin({ email, password }, recordar);
      guardarUsuario(data.usuario);
      guardarUltimoEmail(email);
      set({
        usuario: data.usuario,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
    } catch (err: unknown) {
      const mensaje = _extraerMensajeError(err);
      set({ isLoading: false, error: mensaje, isAuthenticated: false });
      throw err;
    }
  },

  cerrarSesion: async () => {
    const refreshToken = obtenerToken(STORAGE_REFRESH) ?? "";
    try {
      if (refreshToken) await apiLogout(refreshToken);
    } finally {
      limpiarSesion();
      set({ usuario: null, isAuthenticated: false, error: null });
    }
  },
}));

function _extraerMensajeError(err: unknown): string {
  if (
    typeof err === "object" &&
    err !== null &&
    "response" in err &&
    typeof (err as { response?: { data?: { detail?: string } } }).response?.data
      ?.detail === "string"
  ) {
    return (err as { response: { data: { detail: string } } }).response.data
      .detail;
  }
  return "Error al iniciar sesión. Verifique su conexión e intente nuevamente.";
}
