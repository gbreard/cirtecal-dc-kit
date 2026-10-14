"""Fuente aduanera de ARGENTINA (ejemplo de implementación): INDEC, public-api de comercio
exterior. Dato público, sin clave. Sirve de modelo para escribir la del propio país.

Particularidades que conviene saber al adaptar:
- la API responde solo a códigos de 8 dígitos; con 6 dígitos devuelve una lista vacía
  (no un error). Por eso el SA6 completo se pide listando sus subposiciones;
- un código que todavía no existe (o ya no existe) también devuelve una lista vacía: el
  control de códigos vacíos de `aduana.py` lo detecta (versionado de nomenclatura);
- valor = CIF en US$; peso = kg netos; el origen viene con el nombre de INDEC.
"""
from __future__ import annotations

import csv
import json
import urllib.parse
from typing import Iterable

from .. import comun
from . import http
from .aduana_plantilla import FuenteAduana, Registro

API = "https://comexbe.indec.gob.ar/public-api/search/"
PAUSA_S = 2.0


def _digitos(s: str) -> str:
    return "".join(c for c in s if c.isdigit())


class Fuente(FuenteAduana):
    nombre = "INDEC comex (public-api)"

    def __init__(self, nomenclador: str | None = None, periodo: str = "monthly"):
        # nomenclador: CSV con columna 'digitos' (todas las posiciones de la NCM), para
        # abrir un SA6 en sus subposiciones. Opcional; sin él, el espejo usa la canasta.
        self.nomenclador = nomenclador
        self.periodo = periodo

    def _consulta(self, productos: list[str], anio: int, periodo: str) -> list[dict]:
        q = {"commerceType": "import", "year": str(anio), "period": periodo,
             "countryQuery": "allCountries",
             "products": "[" + ",".join(f'"{_digitos(p)}"' for p in productos) + "]",
             "countries": "[]"}
        url = API + "?" + urllib.parse.urlencode(q, safe='[]"')
        return json.loads(http.get(url, PAUSA_S, ipv4=True, cache="indec"))

    def importaciones(self, codigos: list[str], anios: list[int]) -> Iterable[Registro]:
        por_dig = {_digitos(c): c for c in codigos}
        for anio in anios:
            for c in codigos:
                for it in self._consulta([c], anio, self.periodo):
                    dig = _digitos((it.get("product") or {}).get("id", ""))
                    yield Registro(anio, por_dig.get(dig, c),
                                   (it.get("country") or {}).get("name") or "sin_dato",
                                   it.get("amount"), it.get("weight"), it.get("month"))

    def subposiciones(self, sa6: str) -> list[str]:
        d6 = _digitos(sa6)
        if not self.nomenclador:
            return []
        with comun.ruta(self.nomenclador).open(encoding="utf-8") as fh:
            return [r["digitos"] for r in csv.DictReader(fh)
                    if len(r["digitos"]) == 8 and r["digitos"].startswith(d6)]

    def importaciones_sa6(self, sa6: str, anio: int) -> dict[str, float]:
        cods = self.subposiciones(sa6)
        if not cods:
            raise NotImplementedError("falta el nomenclador para abrir el SA6")
        out: dict[str, float] = {}
        for it in self._consulta(cods, anio, "yearly"):
            o = (it.get("country") or {}).get("name") or "sin_dato"
            out[o] = out.get(o, 0.0) + (it.get("amount") or 0.0)
        return out
