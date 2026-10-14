"""Interfaz de la fuente aduanera que cada país implementa.

Un país necesita UNA clase con un método `importaciones(codigos, anios)` que devuelva
registros con cinco campos obligatorios:

    anio     int    año calendario
    codigo   str    código de la nomenclatura nacional, como figura en la canasta
    origen   str    país de origen, con el nombre que usa la aduana ('TOTAL' si no se abre)
    valor_usd float valor CIF en dólares corrientes (None si es secreto: no se imputa)
    kg       float  peso neto en kg (None si es secreto: no se imputa)

Opcional: `mes` (int) si la fuente es mensual. Si la fuente no tiene API, alcanza con
exportar una planilla con esas columnas y usar `ArchivoCSV` (no hace falta programar).

Para el espejo, además, la fuente tiene que poder devolver el SA6 COMPLETO (todas sus
subposiciones nacionales) por origen: `importaciones_sa6(sa6, anio)`. Si no lo implementa,
el espejo compara contra los códigos de la canasta, que es una comparación sesgada (infla
la brecha) y el módulo lo advierte.
"""
from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Iterable

from .. import comun


@dataclass
class Registro:
    anio: int
    codigo: str
    origen: str
    valor_usd: float | None
    kg: float | None
    mes: int | None = None


class FuenteAduana:
    """Clase base. Cada país la hereda e implementa `importaciones`."""
    nombre = "plantilla"

    def importaciones(self, codigos: list[str], anios: list[int]) -> Iterable[Registro]:
        raise NotImplementedError("implementar en kit/fuentes/aduana_<pais>.py")

    def importaciones_sa6(self, sa6: str, anio: int) -> dict[str, float]:
        """Valor CIF del SA6 completo por origen ({origen: usd}). Opcional."""
        raise NotImplementedError


class ArchivoCSV(FuenteAduana):
    """Fuente aduanera desde una planilla ya exportada (anio,codigo,origen,valor_usd,kg[,mes])."""
    nombre = "archivo CSV"

    def __init__(self, archivo: str):
        self.archivo = archivo

    def importaciones(self, codigos=None, anios=None) -> Iterable[Registro]:
        cods = set(codigos) if codigos else None
        for r in comun.leer_csv(self.archivo):
            a = int(r["anio"])
            if (cods and r["codigo"] not in cods) or (anios and a not in anios):
                continue
            yield Registro(a, r["codigo"], r.get("origen") or "TOTAL",
                           comun.num(r.get("valor_usd")), comun.num(r.get("kg")),
                           int(r["mes"]) if r.get("mes") else None)


def desde_config(cfg: dict) -> FuenteAduana:
    """La fuente que declara pais.yaml. Si hay `archivo`, se lee la planilla (no se
    consulta nada); si no, se instancia la clase `Fuente` del módulo declarado."""
    fa = cfg["fuente_aduanera"]
    if fa.get("archivo"):
        return ArchivoCSV(fa["archivo"])
    mod = importlib.import_module(f"kit.fuentes.{fa['modulo']}")
    return mod.Fuente()
