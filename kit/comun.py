"""Utilidades compartidas: rutas, configuración, lectura y escritura de CSV, distancias.

Todo módulo del kit lee la configuración por acá. La raíz del kit es la carpeta que
contiene `config/` y `kit/`; se puede cambiar con la variable de entorno KIT_RAIZ (útil
para tener la configuración de cada país en su propia carpeta).
"""
from __future__ import annotations

import argparse
import csv
import math
import os
from pathlib import Path

import yaml

RAIZ = Path(os.environ.get("KIT_RAIZ", Path(__file__).resolve().parent.parent))


def ruta(rel: str | Path) -> Path:
    """Ruta relativa a la raíz del kit (o absoluta, si ya lo es)."""
    p = Path(rel)
    return p if p.is_absolute() else RAIZ / p


def cargar_yaml(rel: str | Path) -> dict:
    with ruta(rel).open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def pais(rel: str = "config/pais.yaml") -> dict:
    return cargar_yaml(rel)


def parametros(rel: str = "config/parametros.yaml") -> dict:
    return cargar_yaml(rel)


def leer_csv(rel: str | Path) -> list[dict]:
    with ruta(rel).open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def escribir_csv(rel: str | Path, filas: list[dict]) -> str:
    """Escribe un CSV con todas las columnas que aparezcan en las filas (en orden)."""
    p = ruta(rel)
    p.parent.mkdir(parents=True, exist_ok=True)
    campos = list(dict.fromkeys(k for f in filas for k in f)) if filas else ["sin_filas"]
    with p.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=campos)
        w.writeheader()
        w.writerows(filas)
    return str(p)


def salida(nombre: str, cfg: dict | None = None) -> Path:
    """Ruta de un archivo de resultados dentro de la carpeta `salidas` de pais.yaml."""
    cfg = cfg if cfg is not None else pais()
    return ruta(cfg.get("salidas", "salidas/")) / nombre


def num(x) -> float | None:
    """Convierte una celda de CSV en número; vacío o inválido -> None (no se imputa)."""
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip()
    for cand in (s, s.replace(",", ".")):      # admite coma decimal ("12,5")
        try:
            return float(cand)
        except ValueError:
            pass
    return None


def haversine_km(a: tuple, b: tuple) -> float | None:
    """Distancia en km entre dos (lat, lon). None si falta alguna coordenada."""
    if a is None or b is None or None in a or None in b:
        return None
    lat1, lon1, lat2, lon2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = (math.sin((lat2 - lat1) / 2) ** 2
         + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2)
    return 2 * 6371.0088 * math.asin(math.sqrt(h))


def sa6_de(codigo: str) -> str:
    """'8471.50.30' o '84715030' -> '8471.50'. Códigos de 4 dígitos quedan como están."""
    d = "".join(c for c in str(codigo) if c.isdigit())
    return d if len(d) <= 4 else f"{d[:4]}.{d[4:6]}"


def argumentos(descripcion: str) -> argparse.Namespace:
    """Argumentos comunes de línea de comando de cada módulo."""
    ap = argparse.ArgumentParser(description=descripcion)
    ap.add_argument("--pais", default="config/pais.yaml", help="configuración del país")
    ap.add_argument("--parametros", default="config/parametros.yaml")
    return ap.parse_args()
