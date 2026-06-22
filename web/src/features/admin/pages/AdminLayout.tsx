/**
 * Layout del panel admin con navegación lateral responsive.
 * Protege rutas admin — redirige a login si no hay sesión.
 * Sprint 1 — PB-13, PB-18.
 */

import { useEffect, useState } from "react";
import { NavLink, Outlet, useNavigate, useLocation } from "react-router-dom";
import {
  Users,
  Building2,
  ClipboardList,
  LogOut,
  Menu,
  Moon,
  Sun,
  X,
} from "lucide-react";
import { useAuth } from "@/features/auth/hooks/useAuth";
import { useTheme } from "@/shared/hooks/useTheme";
import { ToastContainer } from "@/shared/components";
import styles from "./AdminLayout.module.css";

const ITEMS_NAV = [
  { to: "/admin/usuarios", etiqueta: "Usuarios", Icono: Users },
  { to: "/admin/clientes", etiqueta: "Clientes", Icono: Building2 },
  { to: "/admin/proyectos", etiqueta: "Proyectos", Icono: ClipboardList },
];

function iniciales(nombre: string): string {
  return nombre
    .split(" ")
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase() ?? "")
    .join("");
}

export default function AdminLayout() {
  const { isAuthenticated, usuario, cerrarSesion } = useAuth();
  const { tema, alternarTema } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  // El drawer se abre "en" un pathname específico; si el pathname cambia, queda cerrado.
  const [menuAbiertoEn, setMenuAbiertoEn] = useState<string | null>(null);
  const menuAbierto = menuAbiertoEn === location.pathname;

  useEffect(() => {
    if (!isAuthenticated) {
      navigate("/admin/login", { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const handleLogout = async () => {
    await cerrarSesion();
    navigate("/admin/login", { replace: true });
  };

  if (!isAuthenticated) return null;

  const itemActivo = ITEMS_NAV.find((item) =>
    location.pathname.startsWith(item.to),
  );

  const sidebar = (
    <nav className={styles.nav} aria-label="Navegación principal">
      <div className={styles.marca}>
        <img
          src={tema === "dark" ? "/img/logo-blanco.png" : "/img/logo-negro.png"}
          alt="Wireless HeatMapper"
          className={styles.logoMarca}
        />
        <span>HeatMapper Admin</span>
      </div>

      <ul className={styles.menu} role="list">
        {ITEMS_NAV.map(({ to, etiqueta, Icono }) => (
          <li key={to}>
            <NavLink
              to={to}
              className={({ isActive }) =>
                isActive ? `${styles.enlace} ${styles.activo}` : styles.enlace
              }
            >
              <Icono size={16} aria-hidden="true" />
              {etiqueta}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );

  return (
    <div className={styles.layout}>
      {/* Botón hamburguesa — visible solo en móvil */}
      <button
        className={styles.triggerMovil}
        onClick={() => setMenuAbiertoEn(location.pathname)}
        aria-label="Abrir menú"
        aria-expanded={menuAbierto}
      >
        <Menu size={22} />
      </button>

      {/* Overlay móvil */}
      {menuAbierto && (
        <div
          className={styles.overlay}
          onClick={() => setMenuAbiertoEn(null)}
          aria-hidden="true"
        />
      )}

      {/* Drawer móvil / Sidebar desktop */}
      <div
        className={`${styles.navWrapper} ${menuAbierto ? styles.navAbierto : ""}`}
      >
        <button
          className={styles.cerrarDrawer}
          onClick={() => setMenuAbiertoEn(null)}
          aria-label="Cerrar menú"
        >
          <X size={20} />
        </button>
        {sidebar}
      </div>

      <div className={styles.main}>
        <header className={styles.topbar}>
          <div className={styles.topbarTitulo}>
            {itemActivo && <itemActivo.Icono size={18} aria-hidden="true" />}
            <span>{itemActivo?.etiqueta ?? "Panel"}</span>
          </div>

          <div className={styles.topbarAcciones}>
            <button
              onClick={alternarTema}
              className={styles.iconBtn}
              aria-label={
                tema === "dark"
                  ? "Cambiar a modo claro"
                  : "Cambiar a modo oscuro"
              }
            >
              {tema === "dark" ? (
                <Sun size={16} aria-hidden="true" />
              ) : (
                <Moon size={16} aria-hidden="true" />
              )}
            </button>

            <div className={styles.perfil}>
              <div className={styles.avatar} aria-hidden="true">
                {iniciales(usuario?.nombre ?? "A")}
              </div>
              <span className={styles.nombreUsuario}>
                {usuario?.nombre ?? "Admin"}
              </span>
            </div>

            <button
              onClick={handleLogout}
              className={styles.botonSalir}
              aria-label="Cerrar sesión"
            >
              <LogOut size={14} aria-hidden="true" />
              <span className={styles.botonSalirTexto}>Cerrar sesión</span>
            </button>
          </div>
        </header>

        <main className={styles.contenido}>
          <Outlet />
        </main>
      </div>

      <ToastContainer />
    </div>
  );
}
