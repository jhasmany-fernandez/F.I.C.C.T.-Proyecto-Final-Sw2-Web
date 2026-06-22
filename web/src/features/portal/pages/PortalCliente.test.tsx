import { render, screen } from "@testing-library/react";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import type { PortalClienteOut } from "@/features/admin/types";
import PortalCliente from "./PortalCliente";

vi.mock("@tanstack/react-query", () => ({ useQuery: vi.fn() }));
vi.mock("react-router-dom", () => ({ useParams: vi.fn() }));

const portal: PortalClienteOut = {
  proyecto: {
    id: 1,
    nombre: "Cobertura oficinas Bulldog",
    cliente: "Bulldog Tech.",
    descripcion: null,
  },
  planos: [],
  conjuntos: [
    {
      id: 10,
      plano_id: 2,
      nombre: "APs planta alta",
      proposito: "Validar cobertura del área administrativa",
      descripcion: "Selección aprobada por Bulldog Tech.",
      es_principal: true,
      origen: "manual_web",
      estado_gobernanza: "publicado_cliente",
      creado_por_id: 3,
      cantidad_aps: 1,
      items: [
        {
          bssid: "aa:bb:cc:dd:ee:01",
          ssid: "Bulldog-Admin",
          canal: 44,
          frecuencia_mhz: 5220,
          rssi_promedio: -62,
          pos_x: 120,
          pos_y: 80,
          cantidad_puntos: 8,
        },
      ],
      created_at: "2026-06-20T10:00:00Z",
      updated_at: "2026-06-20T10:00:00Z",
    },
  ],
  heatmaps: [],
  analisis: [],
  escenarios: [],
  reporte_disponible: false,
};

describe("PortalCliente", () => {
  it("muestra el detalle de los conjuntos publicados", () => {
    vi.mocked(useParams).mockReturnValue({ token: "token-publico" });
    vi.mocked(useQuery).mockReturnValue({
      data: portal,
      isLoading: false,
      isError: false,
    } as ReturnType<typeof useQuery>);

    render(<PortalCliente />);

    expect(screen.getByRole("heading", { name: "APs planta alta" })).toBeVisible();
    expect(screen.getByText("Validar cobertura del área administrativa")).toBeVisible();
    expect(screen.getByText(/aa:bb:cc:dd:ee:01/)).toBeVisible();
  });
});
