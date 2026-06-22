"""Firma y verificación de URLs de descarga de planos (HMAC-SHA256).

Formato:
    /api/planos/archivo/{ruta}?exp={timestamp_unix}&sig={hmac_hex}

Donde ``sig = HMAC-SHA256(secret, f"{ruta}|{exp}")``.
"""

import hashlib
import hmac
import time
from urllib.parse import quote


def _calcular_firma(secret: str, ruta: str, exp: int) -> str:
    mensaje = f"{ruta}|{exp}".encode()
    return hmac.new(secret.encode("utf-8"), mensaje, hashlib.sha256).hexdigest()


def generar_url_firmada(
    *,
    ruta_relativa: str,
    secret: str,
    base_url: str = "",
    ttl_seconds: int = 3600,
    now: int | None = None,
) -> str:
    """Genera una URL firmada con expiración.

    Si ``base_url`` es vacío, retorna una URL relativa
    (``/planos/archivo/...?exp=...&sig=...``) lista para que el cliente la
    concatene con su API base. Si se provee, la URL se devuelve absoluta.
    """
    exp = (now if now is not None else int(time.time())) + ttl_seconds
    sig = _calcular_firma(secret, ruta_relativa, exp)
    ruta_url = quote(ruta_relativa, safe="")
    prefijo = base_url.rstrip("/") if base_url else ""
    return f"{prefijo}/planos/archivo/{ruta_url}?exp={exp}&sig={sig}"


def verificar_firma(
    *,
    ruta_relativa: str,
    secret: str,
    exp: int,
    sig: str,
    now: int | None = None,
) -> bool:
    """Retorna True si la firma es válida y la URL no ha expirado."""
    actual = now if now is not None else int(time.time())
    if exp < actual:
        return False
    esperada = _calcular_firma(secret, ruta_relativa, exp)
    return hmac.compare_digest(esperada, sig)
