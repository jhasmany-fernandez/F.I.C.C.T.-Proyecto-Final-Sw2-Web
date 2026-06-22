const STORAGE_ACCESS = "access_token";
const STORAGE_REFRESH = "refresh_token";
const STORAGE_USER = "usuario";
const STORAGE_LAST_EMAIL = "last_login_email";

type PersistenciaSesion = "local" | "session";

function limpiarStorage(storage: Storage) {
  storage.removeItem(STORAGE_ACCESS);
  storage.removeItem(STORAGE_REFRESH);
  storage.removeItem(STORAGE_USER);
}

function obtenerStorageActivo(): Storage | null {
  if (localStorage.getItem(STORAGE_REFRESH)) return localStorage;
  if (sessionStorage.getItem(STORAGE_REFRESH)) return sessionStorage;
  return null;
}

export function guardarSesion(
  accessToken: string,
  refreshToken: string,
  persistencia: PersistenciaSesion,
) {
  const storage = persistencia === "local" ? localStorage : sessionStorage;
  const otroStorage = persistencia === "local" ? sessionStorage : localStorage;

  limpiarStorage(otroStorage);
  storage.setItem(STORAGE_ACCESS, accessToken);
  storage.setItem(STORAGE_REFRESH, refreshToken);
}

export function guardarUsuario(usuario: unknown) {
  const storage = obtenerStorageActivo();
  if (!storage) return;
  storage.setItem(STORAGE_USER, JSON.stringify(usuario));
}

export function guardarUltimoEmail(email: string) {
  localStorage.setItem(STORAGE_LAST_EMAIL, email);
}

export function obtenerUltimoEmail(): string {
  return localStorage.getItem(STORAGE_LAST_EMAIL) ?? "";
}

export function obtenerToken(clave: string): string | null {
  return localStorage.getItem(clave) ?? sessionStorage.getItem(clave);
}

export function obtenerUsuarioGuardado(): string | null {
  return localStorage.getItem(STORAGE_USER) ?? sessionStorage.getItem(STORAGE_USER);
}

export function limpiarSesion() {
  limpiarStorage(localStorage);
  limpiarStorage(sessionStorage);
}

export function haySesionGuardada(): boolean {
  return !!obtenerToken(STORAGE_REFRESH);
}

export { STORAGE_ACCESS, STORAGE_LAST_EMAIL, STORAGE_REFRESH, STORAGE_USER };
