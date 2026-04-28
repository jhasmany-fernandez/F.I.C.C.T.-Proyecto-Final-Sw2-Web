import type { ButtonHTMLAttributes, ReactNode } from "react";
import styles from "./Button.module.css";

type Variant = "primary" | "secondary" | "danger" | "ghost";
type Size = "sm" | "md" | "lg";

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variante?: Variant;
  tamano?: Size;
  isLoading?: boolean;
  fullWidth?: boolean;
  children: ReactNode;
}

export default function Button({
  variante = "primary",
  tamano = "md",
  isLoading = false,
  fullWidth = false,
  disabled,
  children,
  className,
  ...rest
}: Props) {
  const clases = [
    styles.btn,
    styles[variante],
    styles[tamano],
    fullWidth ? styles.fullWidth : "",
    className ?? "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <button {...rest} className={clases} disabled={disabled || isLoading}>
      {isLoading && <span className={styles.spinner} aria-hidden="true" />}
      {children}
    </button>
  );
}
