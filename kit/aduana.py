"""Aduana: serie de importación de la canasta, empalme de códigos, control de códigos
vacíos y deflactor.

Entradas: config/pais.yaml (fuente aduanera, años, enmiendas), config/canasta_sa6.csv y,
si existe, la canasta nacional (config/canasta_<pais>.csv). Salidas en `salidas/`:
  aduana_serie_codigo.csv     año × código: US$, kg, meses, código empalmado
  aduana_serie_capa.csv       año × capa × canasta: US$ nominales y constantes, kg
  aduana_control_codigos.csv  cobertura por código y marca de versionado

Reglas (aprendidas en la corrida argentina):
1. Un código que no devuelve nada no es "importación cero": puede no existir todavía.
   Toda serie que cruce un año de enmienda se lee EMPALMADA (predecesor -> sucesor).
2. Un "máximo histórico" o un "surgimiento" que coincide con una enmienda no se reporta
   hasta descartar el versionado.
3. Las celdas sin valor o sin peso (secreto) no se imputan: quedan fuera de la suma.
4. La canasta "indicativa" (sin línea arancelaria propia) nunca entra a las series.

Uso:  python -m kit.aduana            (lee la fuente que declara pais.yaml)
      python -m kit.aduana --cpiu     (además baja el CPI-U del BLS a config/)
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import date

from . import comun
from .fuentes.aduana_plantilla import Registro, desde_config

BLS_API = "https://api.bls.gov/publicAPI/v1/timeseries/data/"
CPIU = "CUSR0000SA0"      # CPI-U, todos los ítems, desestacionalizado (BLS)
CPIU_ARCHIVO = "config/deflactor_cpiu_anual.csv"


# ---------------------------------------------------------------------------
# Canasta
# ---------------------------------------------------------------------------
def canasta(cfg: dict) -> tuple[dict[str, dict], list[dict]]:
    """(canasta SA6 por código SA6, canasta nacional). Sin canasta nacional, cada SA6 es
    su propio código (el país consulta a 6 dígitos)."""
    sa6 = {r["sa6"]: r for r in comun.leer_csv("config/canasta_sa6.csv")}
    arch = cfg["fuente_aduanera"].get("canasta_nacional")
    if arch:
        nac = comun.leer_csv(arch)
    else:
        nac = [{"codigo_nacional": s, "sa6": s, "sucesor_empalme": "", "sensibilidad": "0"}
               for s in sa6]
    return sa6, nac


# ---------------------------------------------------------------------------
# Serie
# ---------------------------------------------------------------------------
def serie_por_codigo(registros: list[Registro]) -> dict[tuple[str, int], dict]:
    """Suma por (código, año). Cuenta meses con dato y celdas sin peso (no se imputan)."""
    out: dict[tuple, dict] = {}
    for r in registros:
        s = out.setdefault((r.codigo, r.anio), {"valor_usd": 0.0, "kg": 0.0, "meses": set(),
                                                "celdas": 0, "celdas_sin_kg": 0})
        s["valor_usd"] += r.valor_usd or 0.0
        if r.kg is None:
            s["celdas_sin_kg"] += 1
        else:
            s["kg"] += r.kg
        s["celdas"] += 1
        if r.mes:
            s["meses"].add(r.mes)
    return out


def es_parcial(sucesor: str) -> bool:
    """`sucesor_empalme = "ex X"`: una parte del código pasó a X y el código sigue vigente
    (la notación "ex" de las tablas de correlación de la OMA y del Mercosur)."""
    return (sucesor or "").strip().lower().startswith("ex ")


def destino(sucesor: str) -> str:
    """Código de destino de un enlace de empalme, sin el prefijo "ex"."""
    s = (sucesor or "").strip()
    return s[3:].strip() if es_parcial(s) else s


def empalmar(codigo: str, sucesores: dict[str, str]) -> str:
    """Código de la serie empalmada.
    Enlace total (`viejo -> nuevo`): el predecesor se lee como su sucesor (cadenas incl.).
    Enlace parcial (`viejo -> ex nuevo`): el viejo sigue vigente, así que el código nuevo se
    lee junto con el viejo (la serie empalmada es la suma de los dos)."""
    parciales = {destino(v): k for k, v in sucesores.items() if es_parcial(v)}
    totales = {k: v for k, v in sucesores.items() if v and not es_parcial(v)}
    vistos = set()
    while codigo not in vistos:
        vistos.add(codigo)
        if codigo in parciales:
            codigo = parciales[codigo]
        elif totales.get(codigo):
            codigo = totales[codigo]
        else:
            break
    return codigo


def control_codigos(serie: dict, codigos: list[str], anios: tuple[int, int],
                    enmiendas: dict[str, int], sucesores: dict[str, str]) -> list[dict]:
    """Cobertura por código. Marca:
    vacio             nunca devolvió nada (¿código inexistente? ¿mal escrito?)
    nace_en_enmienda  primer dato en un año de enmienda (posterior al inicio de la serie)
    muere_en_enmienda último dato el año previo a una enmienda (antes del fin de la serie)
    sin_empalme       nace o muere en enmienda y no tiene predecesor/sucesor declarado
                      (un enlace parcial "ex X" cuenta como predecesor declarado de X)."""
    años_enm = set(enmiendas.values())
    predecesores = {destino(v): k for k, v in sucesores.items() if v}
    filas = []
    for c in codigos:
        a = sorted(an for (cod, an) in serie if cod == c)
        marcas = []
        if not a:
            marcas.append("vacio")
        else:
            if a[0] > anios[0] and a[0] in años_enm:
                marcas.append("nace_en_enmienda")
                if c not in predecesores:
                    marcas.append("sin_empalme")
            if a[-1] < anios[1] and (a[-1] + 1) in años_enm:
                marcas.append("muere_en_enmienda")
                if not sucesores.get(c) or es_parcial(sucesores[c]):
                    marcas.append("sin_empalme")
        filas.append({"codigo": c, "desde": a[0] if a else None, "hasta": a[-1] if a else None,
                      "anios_con_dato": len(a), "sucesor_empalme": sucesores.get(c, ""),
                      "marcas": ";".join(dict.fromkeys(marcas)) or "ok"})
    return filas


def serie_por_capa(serie: dict, sa6: dict[str, dict], nac: list[dict],
                   sin_sensibles: bool = False) -> list[dict]:
    """Año × capa × canasta. Excluye la canasta indicativa. `sin_sensibles` deja afuera
    los códigos marcados como sensibilidad (se leen las series con y sin ellos)."""
    info = {r["codigo_nacional"]: r for r in nac}
    acc: dict[tuple, list[float]] = defaultdict(lambda: [0.0, 0.0])
    for (c, a), s in serie.items():
        n = info.get(c)
        if n is None:
            continue
        if sin_sensibles and str(n.get("sensibilidad", "0")) == "1":
            continue
        meta = sa6.get(n["sa6"], {})
        if meta.get("canasta") == "indicativa":
            continue
        k = (a, meta.get("capa") or "(sin capa)", meta.get("canasta") or "(sin canasta)")
        acc[k][0] += s["valor_usd"]
        acc[k][1] += s["kg"]
    return [{"anio": a, "capa": capa, "canasta": can, "valor_usd": round(v, 2),
             "kg": round(kg, 1)} for (a, capa, can), (v, kg) in sorted(acc.items())]


# ---------------------------------------------------------------------------
# Deflactor (US$ corrientes -> US$ constantes de un año base, CPI-U)
# ---------------------------------------------------------------------------
def indice_cpiu(archivo: str = CPIU_ARCHIVO) -> dict[int, dict]:
    return {int(r["anio"]): {"indice": float(r["promedio"]), "meses": int(r["meses"])}
            for r in comun.leer_csv(archivo)}


def deflactar(filas: list[dict], base: int, campo: str = "valor_usd",
              indice: dict[int, dict] | None = None) -> list[dict]:
    """Agrega `{campo}_{base}` (constantes) y `deflactor_meses` (<12 = índice parcial).
    El nominal no se toca. Un año base con menos de 11 meses es un error, no se imputa."""
    idx = indice or indice_cpiu()
    if base not in idx or idx[base]["meses"] < 11:
        raise ValueError(f"año base {base} incompleto en el CPI-U")
    out = []
    for r in filas:
        r = dict(r)
        a, v = int(r["anio"]), r.get(campo)
        r[f"{campo}_{base}"] = (round(v * idx[base]["indice"] / idx[a]["indice"], 2)
                                if v is not None and a in idx else None)
        r["deflactor_meses"] = idx.get(a, {}).get("meses")
        out.append(r)
    return out


def descargar_cpiu(desde: int, hasta: int, archivo: str = CPIU_ARCHIVO) -> str:
    """Baja el CPI-U del BLS (API pública v1, <=10 años por consulta) y escribe el
    promedio anual de los meses publicados. Dato de dominio público (gobierno de EE.UU.)."""
    import time
    import requests
    from .fuentes.http import USER_AGENT
    mensual: dict[int, list[float]] = defaultdict(list)
    for a0 in range(desde, hasta + 1, 10):
        r = requests.post(BLS_API, json={"seriesid": [CPIU], "startyear": str(a0),
                                         "endyear": str(min(a0 + 9, hasta))},
                          headers={"User-Agent": USER_AGENT}, timeout=60)
        r.raise_for_status()
        for d in r.json()["Results"]["series"][0]["data"]:
            if d["period"].startswith("M") and d["period"] != "M13" and d["value"] != "-":
                mensual[int(d["year"])].append(float(d["value"]))
        time.sleep(2)
    with comun.ruta(archivo).open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["anio", "promedio", "meses"])
        for a in sorted(mensual):
            w.writerow([a, round(sum(mensual[a]) / len(mensual[a]), 4), len(mensual[a])])
    comun.ruta(archivo + ".fuente.json").write_text(json.dumps(
        {"fuente": "U.S. Bureau of Labor Statistics, serie CUSR0000SA0", "url": BLS_API,
         "fecha_descarga": date.today().isoformat(),
         "metodo": "promedio simple de los meses publicados (columna meses)"},
        ensure_ascii=False, indent=1), encoding="utf-8")
    return archivo


# ---------------------------------------------------------------------------
def correr(cfg: dict) -> dict:
    sa6, nac = canasta(cfg)
    codigos = [r["codigo_nacional"] for r in nac]
    a0, a1 = cfg["anios"]
    regs = list(desde_config(cfg).importaciones(codigos, list(range(a0, a1 + 1))))
    serie = serie_por_codigo(regs)
    suc = {r["codigo_nacional"]: r.get("sucesor_empalme", "") for r in nac}
    base = cfg["fuente_aduanera"].get("deflactor_base", 2025)
    por_codigo = [{"anio": a, "codigo": c, "codigo_empalmado": empalmar(c, suc),
                   "valor_usd": round(s["valor_usd"], 2), "kg": round(s["kg"], 3),
                   "meses": len(s["meses"]) or None, "celdas_sin_kg": s["celdas_sin_kg"]}
                  for (c, a), s in sorted(serie.items(), key=lambda x: (x[0][1], x[0][0]))]
    capa = deflactar(serie_por_capa(serie, sa6, nac), base)
    capa_sin = deflactar(serie_por_capa(serie, sa6, nac, sin_sensibles=True), base)
    for f in capa:
        f["variante"] = "con_sensibles"
    for f in capa_sin:
        f["variante"] = "sin_sensibles"
    ctrl = control_codigos(serie, codigos, (a0, a1),
                           cfg["fuente_aduanera"].get("enmiendas_vigencia", {}), suc)
    return {"serie": serie, "por_codigo": por_codigo, "por_capa": capa + capa_sin,
            "control": ctrl}


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description="Serie de importación de la canasta")
    ap.add_argument("--pais", default="config/pais.yaml")
    ap.add_argument("--cpiu", action="store_true", help="bajar antes el CPI-U del BLS")
    a = ap.parse_args()
    cfg = comun.pais(a.pais)
    if a.cpiu:
        descargar_cpiu(cfg["anios"][0], date.today().year)
    r = correr(cfg)
    for nombre, filas in (("aduana_serie_codigo.csv", r["por_codigo"]),
                          ("aduana_serie_capa.csv", r["por_capa"]),
                          ("aduana_control_codigos.csv", r["control"])):
        print(comun.escribir_csv(comun.salida(nombre, cfg), filas))
    marcados = [c for c in r["control"] if c["marcas"] != "ok"]
    print(f"códigos con marca de versionado o vacíos: {len(marcados)} de {len(r['control'])}")


if __name__ == "__main__":
    main()
