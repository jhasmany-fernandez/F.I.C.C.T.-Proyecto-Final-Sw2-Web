import { ArrowLeft, BrainCircuit, Link2, Network } from "lucide-react";
import { NavLink, Outlet, useLocation, useNavigate, useParams } from "react-router-dom";
import styles from "./ProyectoRFLayout.module.css";

const PESTANAS = [
  {
    path: "conjuntos-ap",
    etiqueta: "Conjuntos AP",
    descripcion: "Revisión y estados de conjuntos móviles, web e IA",
    Icono: Network,
  },
  {
    path: "escenarios-ia",
    etiqueta: "Escenarios IA",
    descripcion: "Generación y revisión de alternativas optimizadas",
    Icono: BrainCircuit,
  },
  {
    path: "publicacion",
    etiqueta: "Publicación",
    descripcion: "Selección explícita de contenido para cliente",
    Icono: Link2,
  },
];

export default function ProyectoRFLayout() {
  const params = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const proyectoId = Number(params.id ?? 0);
  const proyectoNombre =
    (location.state as { proyectoNombre?: string } | null)?.proyectoNombre ??
    `Proyecto #${proyectoId}`;

  return (
    <div>
      <header className={styles.encabezado}>
        <div>
          <button
            className={styles.volver}
            onClick={() => navigate("/admin/proyectos")}
            type="button"
          >
            <ArrowLeft size={16} aria-hidden="true" />
            Proyectos
          </button>
          <h1 className={styles.titulo}>Espacio RF del proyecto</h1>
          <p className={styles.subtitulo}>{proyectoNombre}</p>
        </div>
      </header>

      <nav className={styles.tabs} aria-label="Áreas RF del proyecto">
        {PESTANAS.map(({ path, etiqueta, descripcion, Icono }) => (
          <NavLink
            key={path}
            to={path}
            state={{ proyectoNombre }}
            className={({ isActive }) =>
              isActive ? `${styles.tab} ${styles.tabActiva}` : styles.tab
            }
          >
            <Icono size={18} aria-hidden="true" />
            <span>
              <strong>{etiqueta}</strong>
              <small>{descripcion}</small>
            </span>
          </NavLink>
        ))}
      </nav>

      <Outlet context={{ proyectoId, proyectoNombre }} />
    </div>
  );
}
