"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { Icon } from "@/components/icons";
import { navigationItems } from "@/lib/navigation";

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="sidebar">
      <div className="sidebar__brand">
        <span className="sidebar__brand-mark">
          <Image
            alt="WiFiScope"
            className="sidebar__brand-image"
            height={48}
            priority
            src="/wifiscope-app-icon.png"
            width={48}
          />
        </span>
        <div>
          <strong className="sidebar__brand-title">WiFiScope</strong>
          <p className="sidebar__brand-copy">Storefront y panel operativo</p>
        </div>
      </div>

      <nav className="sidebar__nav" aria-label="Navegacion principal">
        {navigationItems.map((item) => {
          const active =
            item.href === "/"
              ? pathname === item.href
              : pathname.startsWith(item.href);

          return (
            <Link
              key={item.href}
              className={active ? "sidebar__link sidebar__link--active" : "sidebar__link"}
              href={item.href}
            >
              <span className="sidebar__icon">
                <Icon name={item.icon} />
              </span>
              <span>
                <span className="sidebar__label">{item.label}</span>
                <span className="sidebar__description">{item.description}</span>
              </span>
            </Link>
          );
        })}
      </nav>

      <div className="sidebar__footer">
        <p className="sidebar__footer-eyebrow">Launch drop</p>
        <h2 className="sidebar__footer-title">Starter bundles para site survey</h2>
        <p className="sidebar__footer-copy">
          `/settings` ahora abre una portada e-commerce con el icono real de
          WiFiScope y productos listos para demo comercial.
        </p>
        <Link className="sidebar__footer-link" href="/settings">
          Abrir store
        </Link>
      </div>
    </aside>
  );
}
