import { Inbox } from "lucide-react";
import styles from "./EmptyState.module.css";

interface Props {
  mensaje?: string;
  icono?: React.ReactNode;
}

export default function EmptyState({
  mensaje = "No hay registros aún.",
  icono,
}: Props) {
  return (
    <div className={styles.wrapper}>
      <span className={styles.icono} aria-hidden="true">
        {icono ?? <Inbox size={40} strokeWidth={1.5} />}
      </span>
      <p className={styles.mensaje}>{mensaje}</p>
    </div>
  );
}
