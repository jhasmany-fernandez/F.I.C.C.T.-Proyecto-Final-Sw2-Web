import Image from "next/image";

import { Icon } from "@/components/icons";

export function Topbar() {
  return (
    <header className="topbar">
      <label className="topbar__search">
        <Icon className="topbar__search-icon" name="search" />
        <input
          aria-label="Buscar"
          className="topbar__search-input"
          placeholder="Buscar kits, sensores o licencias WiFiScope"
          type="search"
        />
      </label>

      <div className="topbar__actions">
        <button aria-label="Notificaciones" className="icon-button" type="button">
          <Icon name="bell" />
        </button>

        <div className="profile-chip">
          <span className="profile-chip__avatar">
            <Image
              alt="WiFiScope"
              className="profile-chip__avatar-image"
              height={40}
              priority
              src="/wifiscope-app-icon.png"
              width={40}
            />
          </span>
          <span>
            <strong className="profile-chip__name">WiFiScope Store</strong>
            <small className="profile-chip__role">Frontend Next.js</small>
          </span>
        </div>
      </div>
    </header>
  );
}
