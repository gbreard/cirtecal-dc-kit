"""PeeringDB: puntos de intercambio (IXP), sus sedes físicas y las redes por sede.

Común a todos los países. Reglas (términos de uso de PeeringDB, AUP: uso permitido para
"Internet research and analysis"):
- al menos 2 s entre pedidos (anónimo, PeeringDB admite ~10 por minuto: el default es 6 s);
- User-Agent del proyecto, sin correo personal; IPv4;
- el crudo NO se guarda en el repositorio ni se redistribuye en bloque: queda en la caché
  local (KIT_CACHE). Se publican solo resultados derivados, citando "Fuente: PeeringDB".
Clave opcional por variable de entorno PEERINGDB_API_KEY (sube el límite de consultas).

Uso:  python -m kit.fuentes.peeringdb
      -> salidas/ixp_sedes.csv (ixp, sede, fac_id, localidad, lat, lon)
"""
from __future__ import annotations

import json
import os

from .. import comun
from . import http

API = "https://www.peeringdb.com/api"
PAUSA_MIN_S = 2.0
PAUSA_S = max(PAUSA_MIN_S, float(os.environ.get("PEERINGDB_PAUSA_S", 6.0)))


def _consulta(ruta: str) -> list[dict]:
    clave = os.environ.get("PEERINGDB_API_KEY")
    hdr = {"Authorization": f"Api-Key {clave}"} if clave else {}
    return json.loads(http.get(f"{API}/{ruta}", PAUSA_S, headers=hdr, ipv4=True,
                               cache="peeringdb"))["data"]


def sedes_ixp(iso2: str) -> list[dict]:
    """Una fila por (IXP, sede física). 3 consultas: ix, ixfac y fac del país."""
    ix = _consulta(f"ix?country={iso2}")
    if not ix:
        return []
    ixfac = _consulta("ixfac?ix_id__in=" + ",".join(str(x["id"]) for x in ix))
    fac = {f["id"]: f for f in _consulta(f"fac?country={iso2}")}
    nombre = {x["id"]: x["name"] for x in ix}
    filas = []
    for r in sorted(ixfac, key=lambda r: (r["ix_id"], r["fac_id"])):
        f = fac.get(r["fac_id"], {})
        filas.append({"ixp": nombre.get(r["ix_id"]), "ix_id": r["ix_id"], "sede": f.get("name"),
                      "fac_id": r["fac_id"], "localidad": f.get("city"),
                      "lat": f.get("latitude"), "lon": f.get("longitude"),
                      "fuente": "PeeringDB"})
    return filas


def redes_por_facility(fac_ids: list[int]) -> list[dict]:
    """Redes presentes en cada facility (netfac + net). 2 consultas."""
    nf = _consulta("netfac?fac_id__in=" + ",".join(str(i) for i in sorted(fac_ids)))
    if not nf:
        return []
    net = {n["id"]: n for n in _consulta(
        "net?id__in=" + ",".join(str(i) for i in sorted({x["net_id"] for x in nf})))}
    return [{"fac_id": x["fac_id"], "net_id": x["net_id"], "asn": net.get(x["net_id"], {}).get("asn"),
             "red": net.get(x["net_id"], {}).get("name"),
             "info_type": net.get(x["net_id"], {}).get("info_type"), "fuente": "PeeringDB"}
            for x in nf]


def main() -> None:
    a = comun.argumentos("Sedes de IXP del país desde PeeringDB")
    cfg = comun.pais(a.pais)
    print(comun.escribir_csv(comun.salida("ixp_sedes.csv", cfg), sedes_ixp(cfg["iso2"])))


if __name__ == "__main__":
    main()
