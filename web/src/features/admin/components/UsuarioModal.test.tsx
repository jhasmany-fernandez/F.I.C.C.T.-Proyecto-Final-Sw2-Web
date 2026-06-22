import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { UsuarioOut } from "../types";
import UsuarioModal from "./UsuarioModal";

const mockToast = {
  exito: vi.fn(),
  error: vi.fn(),
  info: vi.fn(),
};

const mockCrearUsuario = vi.fn();
const mockActualizarUsuario = vi.fn();
const mockListarUsuarios = vi.fn();
const mockOnCerrar = vi.fn();

vi.mock("../hooks/useUsuarios", () => ({
  USUARIOS_KEY: ["admin", "usuarios"],
  useUsuarios: () => ({
    data: [
      {
        id: 1,
        nombre: "Administrador",
        email: "admin@bulldogtech.bo",
        rol: "admin",
        activo: true,
        created_at: "2026-06-15T00:00:00Z",
      },
    ],
  }),
  useCrearUsuario: () => ({
    mutateAsync: mockCrearUsuario,
    isPending: false,
  }),
  useActualizarUsuario: () => ({
    mutateAsync: mockActualizarUsuario,
    isPending: false,
  }),
}));

vi.mock("../api/usuariosApi", () => ({
  listarUsuarios: () => mockListarUsuarios(),
}));

vi.mock("@/shared/components", async () => {
  const actual = await vi.importActual<typeof import("@/shared/components")>(
    "@/shared/components",
  );

  return {
    ...actual,
    useToast: () => mockToast,
  };
});

function renderModal(usuarioEditar?: UsuarioOut) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <UsuarioModal usuarioEditar={usuarioEditar} onCerrar={mockOnCerrar} />
    </QueryClientProvider>,
  );
}

describe("UsuarioModal", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("cierra el modal si el usuario se creo aunque el POST haya respondido error", async () => {
    mockCrearUsuario.mockRejectedValueOnce(new Error("backend responded 500"));
    mockListarUsuarios.mockResolvedValueOnce([
      {
        id: 1,
        nombre: "Administrador",
        email: "admin@bulldogtech.bo",
        rol: "admin",
        activo: true,
        created_at: "2026-06-15T00:00:00Z",
      },
      {
        id: 2,
        nombre: "Bele Aldana",
        email: "belen@bulldogtech.bo",
        rol: "admin",
        activo: true,
        created_at: "2026-06-15T00:00:00Z",
      },
    ]);

    renderModal();

    fireEvent.change(screen.getByLabelText(/nombre completo/i), {
      target: { value: "Bele Aldana" },
    });
    fireEvent.change(screen.getByLabelText(/correo electrónico/i), {
      target: { value: "belen@bulldogtech.bo" },
    });
    fireEvent.change(screen.getByLabelText(/contraseña inicial/i), {
      target: { value: "Password123!" },
    });

    fireEvent.click(
      screen.getByRole("button", {
        name: /crear cuenta/i,
      }),
    );

    await waitFor(() => {
      expect(mockToast.exito).toHaveBeenCalledWith(
        "Usuario creado correctamente.",
      );
    });

    await waitFor(() => {
      expect(mockOnCerrar).toHaveBeenCalled();
    });
  });

  it("mantiene abierto el modal al entrar en modo edicion", async () => {
    renderModal({
      id: 1,
      nombre: "Administrador",
      email: "admin@bulldogtech.bo",
      rol: "admin",
      activo: true,
      created_at: "2026-06-15T00:00:00Z",
    });

    expect(screen.getByRole("heading", { name: /editar usuario/i })).toBeInTheDocument();

    await waitFor(() => {
      expect(mockOnCerrar).not.toHaveBeenCalled();
    });
  });

  it("no cierra el modal solo por escribir un correo ya existente", async () => {
    renderModal();

    fireEvent.change(screen.getByLabelText(/correo electrónico/i), {
      target: { value: "admin@bulldogtech.bo" },
    });

    expect(screen.getByRole("heading", { name: /nuevo técnico/i })).toBeInTheDocument();

    await waitFor(() => {
      expect(mockOnCerrar).not.toHaveBeenCalled();
    });
  });
});
