/**
 * Hook de tema claro/oscuro (Zustand) con persistencia en localStorage.
 */

import { create } from "zustand";

export type Tema = "light" | "dark";

const STORAGE_KEY = "heatmapper-theme";

function temaPreferidoSistema(): Tema {
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

function temaInicial(): Tema {
  const guardado = localStorage.getItem(STORAGE_KEY);
  return guardado === "light" || guardado === "dark"
    ? guardado
    : temaPreferidoSistema();
}

function aplicarTema(tema: Tema) {
  document.documentElement.setAttribute("data-theme", tema);
  localStorage.setItem(STORAGE_KEY, tema);
}

interface ThemeStore {
  tema: Tema;
  alternarTema: () => void;
  establecerTema: (tema: Tema) => void;
}

export const useTheme = create<ThemeStore>((set, get) => {
  const inicial = temaInicial();
  aplicarTema(inicial);

  return {
    tema: inicial,
    alternarTema: () => {
      const nuevo: Tema = get().tema === "dark" ? "light" : "dark";
      aplicarTema(nuevo);
      set({ tema: nuevo });
    },
    establecerTema: (tema) => {
      aplicarTema(tema);
      set({ tema });
    },
  };
});
