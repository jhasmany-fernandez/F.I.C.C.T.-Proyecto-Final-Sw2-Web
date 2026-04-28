import type { ReactNode } from "react";
import styles from "./Badge.module.css";

type Variante =
  | "activo"
  | "inactivo"
  | "admin"
  | "tecnico"
  | "nuevo"
  | "en_progreso"
  | "completado"
  | "archivado"
  | "neutro";

const ETIQUETAS: Record<Variante, string> = {
  activo: "Activo",
  inactivo: "Inactivo",
  admin: "Admin",
  tecnico: "Técnico",
  nuevo: "Nuevo",
  en_progreso: "En progreso",
  completado: "Completado",
  archivado: "Archivado",
  neutro: "—",
};

interface Props {
  variante: Variante;
  etiqueta?: string;
  icono?: ReactNode;
}

export default function Badge({ variante, etiqueta, icono }: Props) {
  return (
    <span className={`${styles.badge} ${styles[variante]}`}>
      {icono}
      {etiqueta ?? ETIQUETAS[variante]}
    </span>
  );
}
