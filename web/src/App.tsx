import { useEffect } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import LoginAdmin from "@/features/auth/pages/LoginAdmin";
import { useAuth } from "@/features/auth/hooks/useAuth";
import AdminLayout from "@/features/admin/pages/AdminLayout";
import GestionUsuarios from "@/features/admin/pages/GestionUsuarios";
import GestionClientes from "@/features/admin/pages/GestionClientes";
import EscenariosProyecto from "@/features/admin/pages/EscenariosProyecto";
import ListadoProyectosOrg from "@/features/admin/pages/ListadoProyectosOrg";
import ConjuntosAPProyecto from "@/features/admin/pages/ConjuntosAPProyecto";
import ProyectoRFLayout from "@/features/admin/pages/ProyectoRFLayout";
import PublicacionClienteProyecto from "@/features/admin/pages/PublicacionClienteProyecto";
import PortalCliente from "@/features/portal/pages/PortalCliente";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30_000,
    },
  },
});

function AppRoutes() {
  const { cargarSesion } = useAuth();

  useEffect(() => {
    cargarSesion();
  }, [cargarSesion]);

  return (
    <Routes>
      {/* Redirigir raíz a login */}
      <Route path="/" element={<Navigate to="/admin/login" replace />} />

      {/* Auth */}
      <Route path="/admin/login" element={<LoginAdmin />} />

      {/* Panel Admin (protegido en AdminLayout) */}
      <Route path="/admin" element={<AdminLayout />}>
        <Route index element={<Navigate to="/admin/usuarios" replace />} />
        <Route path="usuarios" element={<GestionUsuarios />} />
        <Route path="clientes" element={<GestionClientes />} />
        <Route path="proyectos" element={<ListadoProyectosOrg />} />
        <Route
          path="proyectos/:id/escenarios"
          element={<Navigate to="../rf/escenarios-ia" replace />}
        />
        <Route path="proyectos/:id/rf" element={<ProyectoRFLayout />}>
          <Route index element={<Navigate to="conjuntos-ap" replace />} />
          <Route path="conjuntos-ap" element={<ConjuntosAPProyecto />} />
          <Route path="escenarios-ia" element={<EscenariosProyecto />} />
          <Route path="publicacion" element={<PublicacionClienteProyecto />} />
        </Route>
      </Route>

      {/* Portal cliente publicado por enlace (RP9) */}
      <Route path="/portal/:token" element={<PortalCliente />} />

      <Route path="*" element={<Navigate to="/admin/login" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
