import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import Button from "./Button";

describe("Button", () => {
  it("renderiza su texto y respeta el estado disabled", () => {
    render(
      <Button disabled variante="secondary">
        Guardar
      </Button>,
    );

    expect(
      screen.getByRole("button", {
        name: "Guardar",
      }),
    ).toBeDisabled();
  });

  it("muestra indicador de carga y deshabilita el boton", () => {
    render(<Button isLoading>Creando cuenta</Button>);

    const button = screen.getByRole("button", {
      name: "Creando cuenta",
    });

    expect(button).toBeDisabled();
    expect(button.querySelector("span[aria-hidden='true']")).not.toBeNull();
  });
});
