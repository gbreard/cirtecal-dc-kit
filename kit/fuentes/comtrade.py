"""UN Comtrade: exportaciones que los socios declaran HACIA el país (lado espejo).

Común a todos los países. La clave de suscripción va por variable de entorno
COMTRADE_API_KEY (nunca en el código ni en config). Sin clave se usa el endpoint público
de vista previa (máximo 500 filas por consulta, alcanza para un SA6 × año × socio).

Los crudos quedan en la caché local (KIT_CACHE), FUERA del repositorio: los términos de
uso de Comtrade no permiten redistribuirlos en bloque. Lo que se publica es el resultado
agregado del cruce (`espejo.py`).

Uso:  python -m kit.fuentes.comtrade --sa6 8471.50 8473.30 --anios 2023 2025
      -> salidas/espejo_comtrade.csv (sa6, anio, informante_m49, valor_fob_usd)
"""
from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict

from .. import comun
from . import http

API_CLAVE = "https://comtradeapi.un.org/data/v1/get/C/A/HS"
API_PUBLICA = "https://comtradeapi.un.org/public/v1/preview/C/A/HS"
PAUSA_S = 1.5


def exportaciones_hacia(m49_pais: int, sa6: str, anio: int) -> dict[int, float]:
    """{m49 del informante: valor FOB US$} de lo que cada socio declara exportar al país."""
    clave = os.environ.get("COMTRADE_API_KEY")
    base = API_CLAVE if clave else API_PUBLICA
    cmd = "".join(c for c in sa6 if c.isdigit())
    url = (f"{base}?partnerCode={m49_pais}&period={anio}&cmdCode={cmd}&flowCode=X")
    hdr = {"Ocp-Apim-Subscription-Key": clave} if clave else {}
    datos = json.loads(http.get(url, PAUSA_S, headers=hdr, cache="comtrade")).get("data") or []
    out: dict[int, float] = defaultdict(float)
    for r in datos:
        rep = int(r["reporterCode"])
        if rep != 0:                      # 0 = "Mundo": no es un informante
            out[rep] += r.get("primaryValue") or 0.0
    return dict(out)


def main() -> None:
    ap = argparse.ArgumentParser(description="Lado espejo desde UN Comtrade")
    ap.add_argument("--pais", default="config/pais.yaml")
    ap.add_argument("--sa6", nargs="+", required=True)
    ap.add_argument("--anios", nargs=2, type=int, required=True)
    a = ap.parse_args()
    cfg = comun.pais(a.pais)
    filas = []
    for sa6 in a.sa6:
        for anio in range(a.anios[0], a.anios[1] + 1):
            for m49, v in sorted(exportaciones_hacia(cfg["m49"], sa6, anio).items()):
                filas.append({"sa6": sa6, "anio": anio, "informante_m49": m49,
                              "valor_fob_usd": round(v, 2)})
    print(comun.escribir_csv(comun.salida("espejo_comtrade.csv", cfg), filas))


if __name__ == "__main__":
    main()
