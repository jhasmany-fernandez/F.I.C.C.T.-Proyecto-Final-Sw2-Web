import Image from "next/image";
import Link from "next/link";

const featuredProducts = [
  {
    name: "Sudadera Survey Pro",
    price: "$99.00",
    oldPrice: "$120.00",
    badge: "Oferta",
  },
  {
    name: "Set Signal Runner",
    price: "$99.00",
    oldPrice: "$120.00",
    badge: "Oferta",
  },
  {
    name: "Chaqueta Field Mesh",
    price: "$99.00",
    oldPrice: "$120.00",
    badge: "Oferta",
  },
  {
    name: "Gorra Blue Edition",
    price: "$99.00",
    oldPrice: "$120.00",
    badge: "Oferta",
  },
];

const promoBlocks = [
  {
    title: "Kits inalambricos",
    text: "Paquetes listos para demos, ventas y despliegues comerciales.",
  },
  {
    title: "Accesorios pro",
    text: "Accesorios para campo, reportes y montajes de preventa.",
  },
  {
    title: "Inicio rapido",
    text: "Portada lista para convertirse en catalogo real con pago integrado.",
  },
];

export default function SettingsPage() {
  return (
    <div className="commerce-home">
      <section className="commerce-hero">
        <button aria-label="Anterior" className="commerce-hero__arrow" type="button">
          {"<"}
        </button>

        <div className="commerce-hero__copy">
          <p className="commerce-hero__script">Coleccion WiFiScope</p>
          <h1 className="commerce-hero__title">
            EQUIPAMIENTO INTELIGENTE PARA EQUIPOS WIFI MODERNOS
          </h1>
          <p className="commerce-hero__text">
            Una tienda online horizontal pensada para vender productos,
            paquetes y licencias con una primera impresion mucho mas comercial.
          </p>
          <div className="commerce-hero__actions">
            <Link className="commerce-button commerce-button--dark" href="/dashboard">
              Comprar ahora
            </Link>
          </div>
        </div>

        <div className="commerce-hero__visual">
          <Image
            alt="Visual principal de WiFiScope"
            className="commerce-hero__image"
            height={430}
            priority
            src="/wifiscope-app-icon.png"
            width={430}
          />
        </div>

        <button aria-label="Siguiente" className="commerce-hero__arrow" type="button">
          {">"}
        </button>
      </section>

      <section className="commerce-strip">
        {promoBlocks.map((block) => (
          <article className="commerce-strip__card" key={block.title}>
            <h2>{block.title}</h2>
            <p>{block.text}</p>
          </article>
        ))}
      </section>

      <section className="commerce-collection">
        <div className="commerce-collection__heading">
          <span />
          <h2>Nueva coleccion</h2>
          <span />
        </div>

        <div className="commerce-product-grid">
          {featuredProducts.map((product, index) => (
            <article className="commerce-product-card" key={product.name}>
              <div className="commerce-product-card__media">
                <span className="commerce-product-card__badge">{product.badge}</span>
                <div className={`commerce-product-card__poster commerce-product-card__poster--${index + 1}`}>
                  <Image
                    alt={product.name}
                    className="commerce-product-card__image"
                    height={180}
                    src="/wifiscope-app-icon.png"
                    width={180}
                  />
                </div>
              </div>

              <div className="commerce-product-card__body">
                <h3>{product.name}</h3>
                <div className="commerce-product-card__prices">
                  <strong>{product.price}</strong>
                  <span>{product.oldPrice}</span>
                </div>
                <button className="commerce-button commerce-button--light" type="button">
                  Agregar al carrito
                </button>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
