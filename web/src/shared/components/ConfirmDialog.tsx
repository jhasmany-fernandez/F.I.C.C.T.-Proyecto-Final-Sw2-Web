import Button from "./Button";
import styles from "./ConfirmDialog.module.css";

interface Props {
  titulo: string;
  descripcion?: string;
  textoCancelar?: string;
  textoConfirmar?: string;
  peligroso?: boolean;
  cargando?: boolean;
  onCancelar: () => void;
  onConfirmar: () => void;
}

export default function ConfirmDialog({
  titulo,
  descripcion,
  textoCancelar = "Cancelar",
  textoConfirmar = "Confirmar",
  peligroso = true,
  cargando = false,
  onCancelar,
  onConfirmar,
}: Props) {
  return (
    <div
      className={styles.overlay}
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-titulo"
      onClick={(e) => {
        if (e.target === e.currentTarget) onCancelar();
      }}
    >
      <div className={styles.dialog}>
        <h2 id="confirm-titulo" className={styles.titulo}>
          {titulo}
        </h2>
        {descripcion && <p className={styles.descripcion}>{descripcion}</p>}
        <div className={styles.acciones}>
          <Button variante="secondary" onClick={onCancelar} disabled={cargando}>
            {textoCancelar}
          </Button>
          <Button
            variante={peligroso ? "danger" : "primary"}
            onClick={onConfirmar}
            isLoading={cargando}
          >
            {textoConfirmar}
          </Button>
        </div>
      </div>
    </div>
  );
}
