"""Cliente HTTP responsable (común a todas las fuentes).

Reglas: User-Agent que identifica al proyecto (sin correo personal), pausa mínima entre
pedidos, reintentos con espera creciente, y NUNCA forzar un 403/429: se corta y se avisa.
La caché va FUERA del repositorio (KIT_CACHE, por defecto ~/.cache/kit_cirtecal): los
crudos de terceros no se suben ni se redistribuyen.
"""
from __future__ import annotations

import hashlib
import json
import os
import socket
import time
from contextlib import contextmanager
from datetime import date
from pathlib import Path

USER_AGENT = os.environ.get(
    "KIT_USER_AGENT", "kit-cirtecal/1.0 (investigacion academica; consorcio CIRTECAL)")
CACHE = Path(os.environ.get("KIT_CACHE", Path.home() / ".cache" / "kit_cirtecal"))

_ultimo: dict[str, float] = {}


class Bloqueado(RuntimeError):
    """La fuente respondió 403 o 429: no se insiste ni se intenta esquivarla."""


@contextmanager
def solo_ipv4(activo: bool = True):
    """Fuerza IPv4 (algunos hosts no responden por IPv6 desde ciertas redes)."""
    if not activo:
        yield
        return
    import urllib3.util.connection as uc
    orig = uc.allowed_gai_family
    uc.allowed_gai_family = lambda: socket.AF_INET
    try:
        yield
    finally:
        uc.allowed_gai_family = orig


def get(url: str, pausa_s: float, headers: dict | None = None, intentos: int = 4,
        ipv4: bool = False, cache: str | None = None) -> str:
    """GET con pausa mínima por host, reintentos y caché en disco (fuera del repo).
    `cache`: subcarpeta de CACHE; si el pedido ya está, no se vuelve a consultar."""
    import requests
    if cache:
        clave = hashlib.sha256(url.encode()).hexdigest()[:24]
        archivo = CACHE / cache / f"{clave}.json"
        if archivo.exists():
            return json.loads(archivo.read_text(encoding="utf-8"))["cuerpo"]
    host = url.split("/")[2]
    h = {"User-Agent": USER_AGENT, **(headers or {})}
    ultimo_error = ""
    with solo_ipv4(ipv4):
        for i in range(intentos):
            espera = _ultimo.get(host, 0) + pausa_s - time.monotonic()
            if espera > 0:
                time.sleep(espera)
            try:
                r = requests.get(url, headers=h, timeout=90)
            except requests.RequestException as e:
                ultimo_error = str(e)
                _ultimo[host] = time.monotonic()
                time.sleep(2 * (i + 1))
                continue
            _ultimo[host] = time.monotonic()
            if r.status_code in (403, 429):
                raise Bloqueado(f"{host} respondió {r.status_code}: no se insiste ({url})")
            if r.ok:
                if cache:
                    archivo.parent.mkdir(parents=True, exist_ok=True)
                    archivo.write_text(json.dumps({"url": url, "fecha": date.today().isoformat(),
                                                   "cuerpo": r.text}, ensure_ascii=False),
                                       encoding="utf-8")
                return r.text
            ultimo_error = f"HTTP {r.status_code}"
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"no se pudo leer {url}: {ultimo_error}")
