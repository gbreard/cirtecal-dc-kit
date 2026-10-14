"""Localización: distancias de cada data center a la infraestructura de conectividad y
clasificación de la lógica de localización.

Para cada registro del inventario con coordenada:
  dist_aterrizaje_km     a la estación de amarre de cable submarino más cercana
  dist_nodo_principal_km al nodo principal de intercambio (IXP) del país
  dist_ixp_km            a la sede de IXP más cercana (si hay salidas/ixp_sedes.csv)
  logica                 conectividad  nodo principal a < umbral_nodo_km
                         energia       motivación energética declarada en fuente primaria
                                       (columna motivacion_energetica_fuente del inventario)
                         mixta         ni una ni otra
                         sin_dato      sin coordenada (no se inventa ni se geocodifica una
                                       macrorregión)
  region_principal       dentro / fuera / sin_dato (pais.yaml: region_principal)

La distancia al aterrizaje NO clasifica: si el país tiene un solo punto de amarre es un
dato de país, no una variable por data center.

Salidas: localizacion_dc.csv, localizacion_resumen.csv.   Uso:  python -m kit.localizacion
"""
from __future__ import annotations

from collections import Counter

from . import comun


def _coord(r: dict) -> tuple | None:
    lat, lon = comun.num(r.get("lat")), comun.num(r.get("lon"))
    return (lat, lon) if lat is not None and lon is not None else None


def mas_cercano(p: tuple, puntos: list[dict]) -> tuple[str | None, float | None]:
    mejor = (None, None)
    for q in puntos:
        d = comun.haversine_km(p, (q["lat"], q["lon"]))
        if d is not None and (mejor[1] is None or d < mejor[1]):
            mejor = (q["nombre"], d)
    return mejor


def logica(coord, dist_nodo: float | None, motivacion: str | None, umbral: float) -> str:
    if coord is None or dist_nodo is None:
        return "sin_dato"
    if dist_nodo < umbral:
        return "conectividad"
    if motivacion:
        return "energia"
    return "mixta"


def region(r: dict, dist_nodo: float | None, reg: dict | None, km: float) -> str:
    """Dentro si la entidad es núcleo; en las 'con_umbral' decide la distancia al nodo."""
    if not reg:
        return "sin_dato"
    prov = (r.get("provincia") or "").strip()
    if prov in reg.get("nucleo", []):
        return "dentro"
    if prov in reg.get("con_umbral", []):
        if dist_nodo is None:
            return "sin_dato"
        return "dentro" if dist_nodo <= km else "fuera"
    return "fuera" if prov else "sin_dato"


def calcular(inventario: list[dict], cfg: dict, par_loc: dict,
             sedes_ixp: list[dict] | None = None) -> list[dict]:
    nodo = [{"nombre": cfg["nodo_principal"]["nombre"], "lat": cfg["nodo_principal"]["lat"],
             "lon": cfg["nodo_principal"]["lon"]}]
    amarres = [{"nombre": e["nombre"], "lat": e["lat"], "lon": e["lon"]}
               for e in cfg.get("estaciones_amarre", [])]
    ixp = [{"nombre": f"{s['ixp']} / {s.get('sede') or s.get('localidad')}",
            "lat": comun.num(s["lat"]), "lon": comun.num(s["lon"])}
           for s in (sedes_ixp or []) if comun.num(s.get("lat")) is not None]
    out = []
    for r in inventario:
        p = _coord(r)
        a_n, a_d = mas_cercano(p, amarres) if p else (None, None)
        _, n_d = mas_cercano(p, nodo) if p else (None, None)
        i_n, i_d = mas_cercano(p, ixp) if p and ixp else (None, None)
        out.append({"id": r.get("id"), "nombre": r["nombre"], "estado": r.get("estado"),
                    "provincia": r.get("provincia"), "lat": p[0] if p else None,
                    "lon": p[1] if p else None,
                    "aterrizaje_mas_cercano": a_n,
                    "dist_aterrizaje_km": round(a_d, 1) if a_d is not None else None,
                    "dist_nodo_principal_km": round(n_d, 1) if n_d is not None else None,
                    "ixp_mas_cercano": i_n,
                    "dist_ixp_km": round(i_d, 1) if i_d is not None else None,
                    "logica": logica(p, n_d, r.get("motivacion_energetica_fuente"),
                                     par_loc["umbral_nodo_km"]),
                    "region_principal": region(r, n_d, cfg.get("region_principal"),
                                               par_loc["region_principal_km"])})
    return out


def resumen(filas: list[dict]) -> list[dict]:
    """Conteos por lógica y región, para todos y para los operativos."""
    out = []
    for ambito, fs in (("todos", filas), ("operativos", [f for f in filas
                                                         if f["estado"] == "operativo"])):
        for var in ("logica", "region_principal"):
            for k, n in sorted(Counter(f[var] for f in fs).items()):
                out.append({"ambito": ambito, "variable": var, "valor": k, "n": n})
    return out


def main() -> None:
    a = comun.argumentos("Distancias y lógica de localización")
    cfg, par = comun.pais(a.pais), comun.parametros(a.parametros)
    inv = comun.leer_csv(cfg["inventario"])
    sedes = comun.salida("ixp_sedes.csv", cfg)
    filas = calcular(inv, cfg, par["localizacion"],
                     comun.leer_csv(sedes) if sedes.exists() else None)
    print(comun.escribir_csv(comun.salida("localizacion_dc.csv", cfg), filas))
    print(comun.escribir_csv(comun.salida("localizacion_resumen.csv", cfg), resumen(filas)))


if __name__ == "__main__":
    main()
