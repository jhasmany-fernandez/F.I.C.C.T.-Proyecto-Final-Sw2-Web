import Image from "next/image";
import Link from "next/link";

export default function ForgotPasswordPage() {
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
              <p className="login-card__eyebrow">Recuperacion</p>
              <h1 className="login-card__title">Olvide mi contrasena</h1>
            </div>
          </div>

          <p className="login-card__copy">
            Ingresa tu correo electronico y te enviaremos un enlace para
            restablecer el acceso a tu cuenta.
          </p>

          <form className="login-form">
            <label className="login-form__field">
              <span>Correo electronico</span>
              <input placeholder="correo@ejemplo.com" type="email" />
            </label>

            <button className="login-form__submit" type="submit">
              Enviar enlace
            </button>
          </form>

          <div className="login-card__footer">
            <p>
              Recordaste tu contrasena? <Link href="/login">Volver al login</Link>
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
