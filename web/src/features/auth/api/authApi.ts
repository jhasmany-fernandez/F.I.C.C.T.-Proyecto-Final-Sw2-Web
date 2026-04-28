/** Llamadas a la API de autenticación. Sprint 1 — PB-09. */

import { apiClient, STORAGE_ACCESS, STORAGE_REFRESH } from "@/shared/api/client";
import type { LoginRequest, TokenResponse } from "../types";

export async function login(credentials: LoginRequest): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>(
    "/auth/login",
    credentials
  );
  // Persiste tokens en localStorage
  localStorage.setItem(STORAGE_ACCESS, data.access_token);
  localStorage.setItem(STORAGE_REFRESH, data.refresh_token);
  return data;
}

export async function logout(refreshToken: string): Promise<void> {
  await apiClient.post("/auth/logout", { refresh_token: refreshToken });
  localStorage.removeItem(STORAGE_ACCESS);
  localStorage.removeItem(STORAGE_REFRESH);
}
