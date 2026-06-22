/** Llamadas a la API de autenticación. Sprint 1 — PB-09. */

import { apiClient } from "@/shared/api/client";
import {
  guardarSesion,
  limpiarSesion,
} from "@/shared/api/authStorage";
import type { LoginRequest, TokenResponse } from "../types";

export async function login(
  credentials: LoginRequest,
  recordar: boolean,
): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>(
    "/auth/login",
    credentials
  );
  guardarSesion(
    data.access_token,
    data.refresh_token,
    recordar ? "local" : "session",
  );
  return data;
}

export async function logout(refreshToken: string): Promise<void> {
  await apiClient.post("/auth/logout", { refresh_token: refreshToken });
  limpiarSesion();
}
