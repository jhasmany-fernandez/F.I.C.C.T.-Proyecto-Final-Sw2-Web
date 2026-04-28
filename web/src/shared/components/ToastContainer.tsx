import { CheckCircle, Info, XCircle } from "lucide-react";
import { useToastStore } from "./useToast";
import styles from "./Toast.module.css";

const ICONOS = {
  exito: <CheckCircle size={16} aria-hidden="true" />,
  error: <XCircle size={16} aria-hidden="true" />,
  info: <Info size={16} aria-hidden="true" />,
};

export default function ToastContainer() {
  const toasts = useToastStore((s) => s.toasts);

  if (toasts.length === 0) return null;

  return (
    <div
      className={styles.container}
      role="region"
      aria-label="Notificaciones"
      aria-live="polite"
    >
      {toasts.map((t) => (
        <div key={t.id} className={`${styles.toast} ${styles[t.tipo]}`}>
          <span className={styles.icono}>{ICONOS[t.tipo]}</span>
          <span className={styles.mensaje}>{t.mensaje}</span>
        </div>
      ))}
    </div>
  );
}
