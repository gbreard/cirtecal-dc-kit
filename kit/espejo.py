"""Espejo: lo que los socios declaran exportar al país (Comtrade, FOB) contra lo que
registra la aduana propia (CIF), por SA6, año y origen, y descomposición de la brecha.

Regla clave: comparar SA6 COMPLETO contra SA6 COMPLETO. Si del lado de la aduana se suman
solo los códigos de la canasta, la brecha se infla (se compara un HS6 entero contra un
subconjunto).

Causas (separadas, sin fundir; nada se imputa a la serie de la aduana):
  triangulacion_probable  brecha en un centro de redespacho (Hong Kong, Irlanda, ...)
  atribucion_probable     brecha por país, pero el total SA6 coincide: es origen, no faltante
  secreto_probable        brecha por país alta Y el total SA6 también falta
  secreto_dudoso          zona gris: el total falta pero el país no es extremo (o viceversa)
  valuacion               brecha moderada compatible con FOB vs CIF
  sin_brecha / inmaterial / sin_mapeo
Los umbrales están en config/parametros.yaml; el resultado se lee siempre en los tres
cortes (estricto, base, laxo), porque la causa depende del corte.

Entradas:
  salidas/espejo_comtrade.csv   (de kit.fuentes.comtrade)  sa6, anio, informante_m49, valor_fob_usd
  salidas/espejo_aduana.csv     sa6, anio, origen, valor_cif_usd  (SA6 completo por origen;
                                 lo arma este módulo con `--bajar-aduana` si la fuente
                                 implementa importaciones_sa6, o lo exporta el equipo)
  mapa M49 -> nombre de origen de la aduana (pais.yaml: espejo.mapa_m49)
Salidas: espejo_celdas.csv, espejo_descomposicion.csv.   Uso:  python -m kit.espejo
"""
from __future__ import annotations

from collections import defaultdict

from . import comun

CAUSAS_BRECHA = ("secreto_probable", "secreto_dudoso", "triangulacion_probable",
                 "atribucion_probable")


def umbrales(par_espejo: dict, **cambios) -> dict:
    u = {k: v for k, v in par_espejo.items()
         if k not in ("hubs_m49", "cortes_sensibilidad") and not k.startswith("_")}
    u.update(cambios)
    return u


def clasificar(m49: int, espejo: float, aduana: float | None, sys_ratio: float | None,
               u: dict, hubs: set[int]) -> dict:
    """Causa de la brecha de una celda (SA6 × año × origen). `aduana` None = el informante
    no tiene equivalente en la aduana (sin mapeo); 0 = mapeado y sin importación."""
    if espejo < u["material_usd"]:
        return {"causa": "inmaterial", "ratio": None, "brecha_usd": 0.0}
    if aduana is None:
        return {"causa": "sin_mapeo", "ratio": None, "brecha_usd": 0.0}
    ratio = espejo / aduana if aduana > 0 else None
    brecha = max(espejo - aduana, 0.0)
    fuerte = aduana == 0 or (ratio is not None and ratio >= u["ratio_pais_brecha"])
    if not fuerte:
        if ratio is not None and ratio >= u["ratio_valuacion"]:
            return {"causa": "valuacion", "ratio": ratio, "brecha_usd": brecha}
        return {"causa": "sin_brecha", "ratio": ratio, "brecha_usd": 0.0}
    if m49 in hubs:
        return {"causa": "triangulacion_probable", "ratio": ratio, "brecha_usd": brecha}
    coincide = sys_ratio is not None and sys_ratio < u["sys_atribucion"]
    corto = sys_ratio is None or sys_ratio >= u["sys_secreto"]
    pais_alto = ratio is None or ratio >= u["ratio_pais_secreto"]
    if coincide:
        return {"causa": "atribucion_probable", "ratio": ratio, "brecha_usd": brecha}
    if corto and pais_alto:
        return {"causa": "secreto_probable", "ratio": ratio, "brecha_usd": brecha}
    return {"causa": "secreto_dudoso", "ratio": ratio, "brecha_usd": brecha}


def cruzar(espejo: list[dict], aduana: list[dict], mapa_m49: dict[int, str], u: dict,
           hubs: set[int]) -> list[dict]:
    """Una fila por celda del espejo, con su causa. `espejo`: filas sa6, anio,
    informante_m49, valor_fob_usd. `aduana`: filas sa6, anio, origen, valor_cif_usd."""
    ad: dict[tuple, dict[str, float]] = defaultdict(dict)
    for r in aduana:
        k = (r["sa6"], int(r["anio"]))
        ad[k][r["origen"]] = ad[k].get(r["origen"], 0.0) + (comun.num(r["valor_cif_usd"]) or 0.0)
    tot_esp: dict[tuple, float] = defaultdict(float)
    for r in espejo:
        tot_esp[(r["sa6"], int(r["anio"]))] += comun.num(r["valor_fob_usd"]) or 0.0
    sysr = {k: (te / sum(ad.get(k, {}).values()) if sum(ad.get(k, {}).values()) else None)
            for k, te in tot_esp.items()}
    out = []
    for r in espejo:
        k = (r["sa6"], int(r["anio"]))
        m49 = int(r["informante_m49"])
        nombre = mapa_m49.get(m49)
        valor_ad = (ad.get(k, {}).get(nombre, 0.0)) if nombre else None
        fob = comun.num(r["valor_fob_usd"]) or 0.0
        c = clasificar(m49, fob, valor_ad, sysr.get(k), u, hubs)
        out.append({"sa6": k[0], "anio": k[1], "informante_m49": m49, "origen_aduana": nombre,
                    "espejo_fob_usd": round(fob, 2),
                    "aduana_cif_usd": round(valor_ad, 2) if valor_ad is not None else None,
                    "ratio": round(c["ratio"], 2) if c["ratio"] is not None else None,
                    "sys_ratio": round(sysr[k], 2) if sysr.get(k) is not None else None,
                    "brecha_usd": round(c["brecha_usd"], 2), "causa": c["causa"],
                    "confianza": "estimada", "nota": "espejo FOB vs aduana CIF"})
    return out


def descomposicion(celdas: list[dict], corte: str) -> list[dict]:
    """Brecha total y celdas por causa (solo causas de brecha)."""
    acc: dict[str, list[float]] = defaultdict(lambda: [0, 0.0])
    for c in celdas:
        if c["causa"] in CAUSAS_BRECHA:
            acc[c["causa"]][0] += 1
            acc[c["causa"]][1] += c["brecha_usd"]
    return [{"corte": corte, "causa": k, "celdas": acc[k][0], "brecha_usd": round(acc[k][1])}
            for k in CAUSAS_BRECHA if k in acc]


def correr(cfg: dict, par: dict, espejo: list[dict], aduana: list[dict]) -> dict:
    pe = par["espejo"]
    hubs = {int(k) for k in pe["hubs_m49"]}
    mapa = {int(r["m49"]): r["origen"] for r in comun.leer_csv(cfg["espejo"]["mapa_m49"])}
    cortes = {"base": umbrales(pe)}
    for nombre, cambios in (pe.get("cortes_sensibilidad") or {}).items():
        cortes[nombre] = umbrales(pe, **cambios)
    celdas = cruzar(espejo, aduana, mapa, cortes["base"], hubs)
    desc = []
    for nombre, u in cortes.items():
        desc += descomposicion(cruzar(espejo, aduana, mapa, u, hubs), nombre)
    return {"celdas": celdas, "descomposicion": desc}


def bajar_aduana(cfg: dict, sa6s: list[str], anios: tuple[int, int]) -> list[dict]:
    """Lado aduana a SA6 completo, si la fuente del país implementa importaciones_sa6."""
    from .fuentes.aduana_plantilla import desde_config
    f = desde_config(cfg)
    filas = []
    for s in sa6s:
        for a in range(anios[0], anios[1] + 1):
            for o, v in sorted(f.importaciones_sa6(s, a).items()):
                filas.append({"sa6": s, "anio": a, "origen": o, "valor_cif_usd": v})
    return filas


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description="Cruce espejo y descomposición de la brecha")
    ap.add_argument("--pais", default="config/pais.yaml")
    ap.add_argument("--parametros", default="config/parametros.yaml")
    ap.add_argument("--bajar-aduana", action="store_true",
                    help="armar espejo_aduana.csv con la fuente del país (SA6 completo)")
    a = ap.parse_args()
    cfg, par = comun.pais(a.pais), comun.parametros(a.parametros)
    if not comun.salida("espejo_comtrade.csv", cfg).exists():
        raise SystemExit("falta salidas/espejo_comtrade.csv: correr antes "
                         "`python -m kit.fuentes.comtrade --sa6 ... --anios A0 A1`")
    esp = comun.leer_csv(comun.salida("espejo_comtrade.csv", cfg))
    if a.bajar_aduana:
        sa6s = sorted({r["sa6"] for r in esp})
        anios = sorted({int(r["anio"]) for r in esp})
        comun.escribir_csv(comun.salida("espejo_aduana.csv", cfg),
                           bajar_aduana(cfg, sa6s, (anios[0], anios[-1])))
    if not comun.salida("espejo_aduana.csv", cfg).exists():
        raise SystemExit("falta salidas/espejo_aduana.csv (sa6, anio, origen, valor_cif_usd, "
                         "SA6 COMPLETO): exportarlo de la aduana o usar --bajar-aduana")
    ad = comun.leer_csv(comun.salida("espejo_aduana.csv", cfg))
    r = correr(cfg, par, esp, ad)
    print(comun.escribir_csv(comun.salida("espejo_celdas.csv", cfg), r["celdas"]))
    print(comun.escribir_csv(comun.salida("espejo_descomposicion.csv", cfg), r["descomposicion"]))


if __name__ == "__main__":
    main()
