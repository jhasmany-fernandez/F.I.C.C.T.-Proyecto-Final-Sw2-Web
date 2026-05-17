import { create } from "zustand";

export type ToastTipo = "exito" | "error" | "info";

export interface ToastItem {
  id: string;
  mensaje: string;
  tipo: ToastTipo;
}

interface ToastStore {
  toasts: ToastItem[];
  agregar: (mensaje: string, tipo?: ToastTipo) => void;
  quitar: (id: string) => void;
}

export const useToastStore = create<ToastStore>((set) => ({
  toasts: [],
  agregar: (mensaje, tipo = "exito") => {
    const id = generarToastId();
    set((s) => ({ toasts: [...s.toasts, { id, mensaje, tipo }] }));
    setTimeout(() => {
      set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }));
    }, 3500);
  },
  quitar: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}));

function generarToastId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }

  if (typeof crypto !== "undefined" && typeof crypto.getRandomValues === "function") {
    const bytes = new Uint32Array(2);
    crypto.getRandomValues(bytes);
    return `toast-${bytes[0].toString(16)}${bytes[1].toString(16)}`;
  }

  return `toast-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

/** Hook conveniente para emitir toasts desde cualquier componente */
export function useToast() {
  const agregar = useToastStore((s) => s.agregar);
  return {
    exito: (msg: string) => agregar(msg, "exito"),
    error: (msg: string) => agregar(msg, "error"),
    info: (msg: string) => agregar(msg, "info"),
  };
}
