import { useEffect } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import LoginAdmin from "@/features/auth/pages/LoginAdmin";
import { useAuth } from "@/features/auth/hooks/useAuth";
import AdminLayout from "@/features/admin/pages/AdminLayout";
import GestionUsuarios from "@/features/admin/pages/GestionUsuarios";
import GestionClientes from "@/features/admin/pages/GestionClientes";
import ListadoProyectosOrg from "@/features/admin/pages/ListadoProyectosOrg";

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
      </Route>

      {/* Portal cliente — pendiente Sprint 6 (RP9) */}
      <Route
        path="/portal/:token"
        element={<div>Portal Cliente — pendiente RP9</div>}
      />

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
