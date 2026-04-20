import Image from "next/image";
import Link from "next/link";

export default function LoginPage() {
  return (
    <section className="login-page">
      <div className="login-page__window">
        <div className="login-card">
          <div className="login-card__brand">
            <Image
              alt="WiFiScope"
              className="login-card__logo"
              height={72}
              priority
              src="/wifiscope-app-icon.png"
              width={72}
            />
            <div>
              <p className="login-card__eyebrow">Acceso privado</p>
              <h1 className="login-card__title">Bienvenido</h1>
            </div>
          </div>

          <p className="login-card__copy">
            Inicia sesion para continuar con tu tienda WiFiScope y el panel tecnico.
          </p>

          <form className="login-form">
            <label className="login-form__field">
              <span>Correo electronico</span>
              <input placeholder="correo@ejemplo.com" type="email" />
            </label>

            <label className="login-form__field">
              <span>Contrasena</span>
              <div className="login-form__password">
                <input placeholder="Ingresa tu contrasena" type="password" />
                <button aria-label="Mostrar contrasena" type="button">
                  Ver
                </button>
              </div>
            </label>

            <button className="login-form__submit" type="submit">
              Ingresar
            </button>
          </form>

          <div className="login-card__footer">
            <Link href="/forgot-password">Olvide mi contrasena</Link>
            <p>
              No tienes cuenta? <Link href="/settings">Explora la tienda</Link>
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
