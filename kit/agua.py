"""Consumo de agua de centros de datos: directa (en sitio) e indirecta (generación).

    agua directa   = energía IT    × WUE de la tecnología de refrigeración
    agua indirecta = energía TOTAL × intensidad hídrica del suministro eléctrico
    energía total  = energía IT × PUE

Todo es consumo (agua que no vuelve a la fuente), no extracción. La evaporación de los
embalses hidroeléctricos se informa en una columna aparte (`indirecta_embalse_hm3`): su
asignación a la generación está discutida, y en una matriz con mucha hidro domina el total.

Cada coeficiente es una banda [bajo, central, alto] (config/parametros.yaml, agua). Las
bandas se combinan extremo con extremo: el escenario bajo usa los tres valores bajos (energía,
WUE e intensidad) y el alto los tres altos. Escenarios de refrigeración: seco, mixto y
evaporativo; qué tecnología es cada uno depende del perfil (aire o líquido).

Casos y matriz del país en config/pais.yaml (agua_casos, matriz_generacion, agua_urbana).
Salida: salidas/agua_banda.csv.   Uso:  python -m kit.agua
"""
from __future__ import annotations

from . import comun

BANDA = ("bajo", "central", "alto")
HORAS = 8760


def intensidad_matriz(par_agua: dict, matriz: dict) -> dict[str, dict[str, float]]:
    """Intensidad hídrica de la generación (L/kWh), ponderada por la matriz, por escenario:
    {esc: {"sin_embalse": L/kWh, "embalse": L/kWh}}. hidro_menor usa el coeficiente de hidro."""
    gen = par_agua["generacion_l_kwh"]
    embalse = set(par_agua.get("tecnologias_embalse", []))
    gwh = matriz["gwh"]
    tot = sum(gwh.values())
    out = {}
    for i, esc in enumerate(BANDA):
        s = {"sin_embalse": 0.0, "embalse": 0.0}
        for tec, g in gwh.items():
            coef = gen.get(tec) or gen["hidro" if tec == "hidro_menor" else tec]
            s["embalse" if tec in embalse else "sin_embalse"] += g / tot * coef["banda"][i]
        out[esc] = s
    return out


def intensidad_tecnologia(par_agua: dict, tec: str) -> dict[str, dict[str, float]]:
    """Intensidad de un suministro de una sola tecnología (p. ej. generación propia a gas)."""
    b = par_agua["generacion_l_kwh"][tec]["banda"]
    emb = tec in par_agua.get("tecnologias_embalse", [])
    return {esc: {"sin_embalse": 0.0 if emb else b[i], "embalse": b[i] if emb else 0.0}
            for i, esc in enumerate(BANDA)}


def energias(caso: dict) -> dict[str, tuple[float, float]]:
    """{esc: (GWh IT, GWh total)} en operación continua."""
    out = {}
    for i, esc in enumerate(BANDA):
        pue = caso["pue"][i]
        if caso["base_mw"] == "IT":
            it = caso["mw"] * HORAS / 1000
            out[esc] = (it, it * pue)
        else:
            tot = caso["mw"] * HORAS / 1000
            out[esc] = (tot / pue, tot)
    return out


def calcular(caso_id: str, e: dict, par_agua: dict, perfil: str, intens: dict,
             suministro: str, urbana: dict | None = None) -> list[dict]:
    """Filas por escenario de refrigeración × banda. `e`: {esc: (GWh IT, GWh total)}."""
    wue = par_agua["wue_l_kwh_it"]
    filas = []
    for refr, tec in par_agua["escenarios_refrigeracion"][perfil].items():
        for i, esc in enumerate(BANDA):
            it, tot = e[esc]
            w = wue[tec]["banda"][i]
            dire = it * 1e6 * w / 1e9                      # GWh -> kWh; L -> hm³
            ind = tot * 1e6 * intens[esc]["sin_embalse"] / 1e9
            emb = tot * 1e6 * intens[esc]["embalse"] / 1e9
            f = {"caso": caso_id, "perfil": perfil, "suministro": suministro,
                 "refrigeracion": refr, "tecnologia_refrigeracion": tec, "banda": esc,
                 "energia_it_gwh": round(it, 1), "energia_total_gwh": round(tot, 1),
                 "wue_l_kwh_it": w,
                 "intensidad_l_kwh": round(intens[esc]["sin_embalse"], 3),
                 "intensidad_embalse_l_kwh": round(intens[esc]["embalse"], 3),
                 "directa_hm3": round(dire, 6), "indirecta_hm3": round(ind, 6),
                 "total_hm3": round(dire + ind, 6),
                 "indirecta_embalse_hm3": round(emb, 6),
                 "parte_directa": round(dire / (dire + ind), 3) if dire + ind else None,
                 "estado_wue": wue[tec].get("_estado", "")}
            if urbana:
                lhd = urbana["l_hab_dia"][1]
                f["habitantes_equiv_directa"] = round(dire * 1e9 / (lhd * 365))
                # con 495 L/hab/día (producida) da menos habitantes; con 180, más
                f["habitantes_equiv_rango"] = (
                    f"{round(dire * 1e9 / (max(urbana['l_hab_dia']) * 365))}–"
                    f"{round(dire * 1e9 / (min(urbana['l_hab_dia']) * 365))}")
            filas.append(f)
    return filas


def correr(cfg: dict, par: dict) -> list[dict]:
    pa = par["agua"]
    matriz = cfg.get("matriz_generacion")
    if not matriz:
        raise SystemExit("pais.yaml no tiene matriz_generacion: no se puede calcular el agua "
                         "indirecta (completar o correr solo la directa).")
    red = intensidad_matriz(pa, matriz)
    urb = cfg.get("agua_urbana")
    filas = []
    for caso in cfg.get("agua_casos", []):
        e = energias(caso)
        filas += calcular(caso["id"], e, pa, caso["perfil"], red, "red", urb)
        for tec in caso.get("suministro_propio", []):
            filas += calcular(caso["id"], e, pa, caso["perfil"],
                              intensidad_tecnologia(pa, tec), f"propio_{tec}", urb)
    return filas


def main() -> None:
    a = comun.argumentos("Consumo de agua directo e indirecto")
    cfg, par = comun.pais(a.pais), comun.parametros(a.parametros)
    print(comun.escribir_csv(comun.salida("agua_banda.csv", cfg), correr(cfg, par)))


if __name__ == "__main__":
    main()
