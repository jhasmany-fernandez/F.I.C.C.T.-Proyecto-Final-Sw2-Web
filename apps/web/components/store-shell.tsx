"use client";

import type { ReactNode } from "react";
import Image from "next/image";
import Link from "next/link";

const primaryLinks = [
  { href: "/settings", label: "Inicio" },
  { href: "/dashboard", label: "Nosotros" },
  { href: "/measurements", label: "Movil" },
  { href: "/scans", label: "Audio" },
  { href: "/floor-plans", label: "Ropa" },
  { href: "/reports", label: "Relojes" },
];

export function StoreShell({ children }: { children: ReactNode }) {
  return (
    <div className="store-shell">
      <div className="store-topbar">
        <div className="store-topbar__container">
          <p className="store-topbar__call">Llama ahora: (+591) 72992000</p>
          <div className="store-topbar__links">
            <a href="#">Soporte</a>
            <a href="#">Tiendas</a>
            <a href="#">Envio gratis</a>
          </div>
        </div>
      </div>

      <header className="store-header">
        <div className="store-header__container">
          <Link className="store-logo" href="/settings">
            <Image
              alt="WiFiScope"
              className="store-logo__image"
              height={64}
              priority
              src="/wifiscope-app-icon.png"
              width={64}
            />
            <span className="store-logo__text">
              <strong>WiFiScope</strong>
              <small>Solucion de tienda</small>
            </span>
          </Link>

          <div className="store-search">
            <button className="store-search__category" type="button">
              Todas las categorias
            </button>
            <input
              aria-label="Buscar productos"
              className="store-search__input"
              placeholder="Busca tu producto..."
              type="search"
            />
            <button className="store-search__submit" type="button">
              Buscar
            </button>
          </div>

          <div className="store-header__actions">
            <Link className="store-account" href="/login">
              Mi cuenta
            </Link>
          </div>
        </div>
      </header>

      <nav className="store-nav" aria-label="Categorias de la tienda">
        <div className="store-nav__container">
          <div className="store-nav__links">
            {primaryLinks.map((item) => (
              <Link key={item.label} href={item.href}>
                {item.label}
              </Link>
            ))}
            <a href="#">Blog</a>
            <a href="#">Contacto</a>
          </div>

          <div className="store-cart">
            <span>Carrito</span>
            <strong>0</strong>
          </div>
        </div>
      </nav>

      <main className="store-page">{children}</main>

      <footer className="store-footer">
        <div className="store-footer__container">
          <p>Tienda WiFiScope</p>
        </div>
      </footer>
    </div>
  );
}
