import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import GestionClientes from "./GestionClientes";

const mockToast = {
  exito: vi.fn(),
  error: vi.fn(),
  info: vi.fn(),
};

const mockCrearCliente = vi.fn();
const mockActualizarCliente = vi.fn();
const mockDesactivarCliente = vi.fn();
const mockListarTodosClientes = vi.fn();

vi.mock("../hooks/useClientes", () => ({
  CLIENTES_KEY: ["admin", "clientes"],
  useClientes: () => ({
    data: [
      {
        id: 1,
        nombre: "Bulldog Tech.",
        activo: true,
        created_at: "2026-06-15T00:00:00Z",
      },
    ],
    isLoading: false,
    isError: false,
  }),
  useCrearCliente: () => ({
    mutateAsync: mockCrearCliente,
    isPending: false,
  }),
  useActualizarCliente: () => ({
    mutateAsync: mockActualizarCliente,
  }),
  useDesactivarCliente: () => ({
    mutateAsync: mockDesactivarCliente,
  }),
}));

vi.mock("../api/clientesApi", () => ({
  listarTodosClientes: () => mockListarTodosClientes(),
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

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <GestionClientes />
    </QueryClientProvider>,
  );
}

describe("GestionClientes", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("cierra el modal si el cliente se creo aunque el POST haya respondido error", async () => {
    mockCrearCliente.mockRejectedValueOnce(new Error("backend responded 500"));
    mockListarTodosClientes.mockResolvedValueOnce([
      {
        id: 1,
        nombre: "Bulldog Tech.",
        activo: true,
        created_at: "2026-06-15T00:00:00Z",
      },
      {
        id: 2,
        nombre: "Nuevatel S.R.L.",
        activo: true,
        created_at: "2026-06-15T00:00:00Z",
      },
    ]);

    renderPage();

    fireEvent.click(
      screen.getByRole("button", {
        name: /nuevo cliente/i,
      }),
    );

    fireEvent.change(screen.getByLabelText(/nombre del cliente/i), {
      target: { value: "Nuevatel S.R.L." },
    });

    fireEvent.click(
      screen.getByRole("button", {
        name: /crear cliente/i,
      }),
    );

    await waitFor(() => {
      expect(mockToast.exito).toHaveBeenCalledWith(
        'Cliente "Nuevatel S.R.L." creado correctamente.',
      );
    });

    await waitFor(() => {
      expect(
        screen.queryByRole("heading", { name: /nuevo cliente/i }),
      ).not.toBeInTheDocument();
    });
  });

  it("cierra el modal si el backend responde 409 pero el cliente ya aparece al revalidar", async () => {
    mockCrearCliente.mockRejectedValueOnce({
      response: {
        status: 409,
      },
    });
    mockListarTodosClientes.mockResolvedValueOnce([
      {
        id: 1,
        nombre: "Bulldog Tech.",
        activo: true,
        created_at: "2026-06-15T00:00:00Z",
      },
      {
        id: 5,
        nombre: "Tigo Bolivia",
        activo: true,
        created_at: "2026-06-15T00:00:00Z",
      },
    ]);

    renderPage();

    fireEvent.click(
      screen.getByRole("button", {
        name: /nuevo cliente/i,
      }),
    );

    fireEvent.change(screen.getByLabelText(/nombre del cliente/i), {
      target: { value: "Tigo Bolivia" },
    });

    fireEvent.click(
      screen.getByRole("button", {
        name: /crear cliente/i,
      }),
    );

    await waitFor(() => {
      expect(mockToast.info).toHaveBeenCalledWith(
        'El cliente "Tigo Bolivia" ya existe en el sistema.',
      );
    });

    await waitFor(() => {
      expect(
        screen.queryByRole("heading", { name: /nuevo cliente/i }),
      ).not.toBeInTheDocument();
    });
  });

  it("mantiene abierto el editor al hacer click en editar", async () => {
    renderPage();

    fireEvent.click(
      screen.getByRole("button", {
        name: /editar/i,
      }),
    );

    expect(
      screen.getByRole("heading", { name: /editar cliente/i }),
    ).toBeInTheDocument();

    await waitFor(() => {
      expect(
        screen.getByRole("textbox", { name: /nombre del cliente/i }),
      ).toHaveValue("Bulldog Tech.");
    });
  });
});
