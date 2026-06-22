/**
 * Cliente HTTP centralizado (Axios) para el panel admin.
 * Maneja JWT automáticamente e intercepta 401 para refresh.
 * Sprint 1 — PB-13, PB-18.
 */

import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";

const STORAGE_ACCESS = "access_token";
const STORAGE_REFRESH = "refresh_token";

export const apiClient = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

// ── Interceptor de request: adjunta Bearer token ──────────────────────────
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem(STORAGE_ACCESS);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── Interceptor de response: refresca token en 401 ─────────────────────────
let isRefreshing = false;
let pendingQueue: Array<{
  resolve: (value: unknown) => void;
  reject: (reason?: unknown) => void;
}> = [];

const procesarCola = (error: unknown, token: string | null) => {
  pendingQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error);
    } else {
      resolve(token);
    }
  });
  pendingQueue = [];
};

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    if (error.response?.status === 401 && !originalRequest._retry) {
      const refreshToken = localStorage.getItem(STORAGE_REFRESH);

      if (!refreshToken) {
        _redirigirALogin();
        return Promise.reject(error);
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          pendingQueue.push({ resolve, reject });
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return apiClient(originalRequest);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const { data } = await axios.post<{ access_token: string }>(
          "/api/auth/refresh",
          { refresh_token: refreshToken },
        );
        localStorage.setItem(STORAGE_ACCESS, data.access_token);
        apiClient.defaults.headers.common.Authorization = `Bearer ${data.access_token}`;
        procesarCola(null, data.access_token);
        originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        procesarCola(refreshError, null);
        _redirigirALogin();
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  },
);

function _redirigirALogin() {
  localStorage.removeItem(STORAGE_ACCESS);
  localStorage.removeItem(STORAGE_REFRESH);
  localStorage.removeItem("usuario");
  // Evitar redirección en bucle si ya estamos en login
  if (!window.location.pathname.includes("/admin/login")) {
    window.location.href = "/admin/login";
  }
}

export { STORAGE_ACCESS, STORAGE_REFRESH };
