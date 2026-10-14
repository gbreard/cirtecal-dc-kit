"""Potencia (MW) -> equipo (BoM) -> aduana, y factor de atribución del RAEE a data centers.

Dos vías que se corren juntas:
  física (de abajo hacia arriba):  MW_IT × reparto de potencia ÷ kW por unidad -> unidades -> kg
  económica (de arriba hacia abajo): MW_IT × US$/MW × reparto del capex -> US$ por subsistema
Si difieren en más de `tolerancia_vias` (factor 3) hay un supuesto roto y se marca.

El equipo esperado se contrasta con la importación observada (aduana) por familia de
códigos y en una ventana de varios años: la infraestructura se compra una vez; el IT se
repone con la vida media del escenario central.

Factor de atribución (f): qué fracción de la masa IT importada por año corresponde a la
reposición del parque de data centers.
    f = Σ_familia stock_IT_DC / vida_media(tipo, escenario)  ÷  masa IT limpia importada por año
    RAEE_DC = f × RAEE_IT (raee.py), con el MISMO escenario de vida en los dos factores.
f se reporta sin redondear en el cálculo; el CSV lo muestra con 4 decimales.

Casos: el parque de referencia nacional (pais.yaml: parque_referencia), el inventario
propio (operativos > 1 MW) y los anuncios de hiperescala del inventario (perfil IA,
cota superior de lo que ya se importó). Nunca se infieren MW de inversión, m² o kVA.

Salidas en `salidas/`: mwbom_componentes.csv, mwbom_vs_aduana.csv,
mwbom_reconciliacion.csv, atribucion_dc.csv.   Uso:  python -m kit.mwbom
"""
from __future__ import annotations

from collections import defaultdict

from . import comun
from .raee import ESCENARIOS as ESC_VIDA, vida_media

ESC_BOM = ("bajo", "central", "alto")      # bajo = menos kg por MW


def mw_it(caso: dict, par: dict) -> float:
    """MW IT del caso. Si el MW declarado es bruto, MW_IT = MW / PUE del perfil."""
    if caso["base_mw"] == "IT":
        return caso["mw"]
    return caso["mw"] / par["perfiles"][caso["perfil"]]["pue"]


def bom_fisico(caso: dict, esc: str, par: dict) -> list[dict]:
    """Componentes por vía física para (caso, escenario del BoM)."""
    perfil = par["perfiles"][caso["perfil"]]
    U = par["unidades"]
    it_kw = mw_it(caso, par) * 1000
    gross_kw = it_kw * perfil["pue"]
    red = par["redundancia"][perfil["redundancia"]]
    rep = par["reparto_it"]
    tot = sum(rep.values())
    kw_srv = it_kw * rep["servidores"] / tot
    arq = perfil["arquitectura"][esc]
    filas = []

    def add(sub, comp, unidades, kg_u, usd_u, familia):
        filas.append({"subsistema": sub, "componente": comp, "unidades": unidades,
                      "masa_kg": unidades * kg_u, "valor_usd_est": unidades * usd_u,
                      "familia": familia})

    g, sg, sc = arq["share_gpu"], U[arq["servidor_gpu"]], U["servidor_cpu"]
    add("IT", "servidor_cpu", kw_srv * (1 - g) / sc["kw"], sc["kg"], sc["usd"], "servidores")
    add("IT", arq["servidor_gpu"], kw_srv * g / sg["kw"], sg["kg"], sg["usd"], "servidores")
    add("IT", "almacenamiento", it_kw * rep["almacenamiento"] / tot / U["almacenamiento"]["kw"],
        U["almacenamiento"]["kg"], U["almacenamiento"]["usd"], "almacenamiento")
    add("IT", "switch", it_kw * rep["red"] / tot / U["switch"]["kw"],
        U["switch"]["kg"], U["switch"]["usd"], "red")
    add("IT", "rack_vacio", it_kw / perfil["kw_rack"][esc], U["rack_vacio"]["kg"],
        U["rack_vacio"]["usd"], "racks")
    ups_kw = it_kw * red
    add("Energía", "ups", ups_kw, U["ups"]["kg_kw"], U["ups"]["usd_kw"], "ups")
    b = U["bateria_" + perfil["bateria"]]
    add("Energía", "bateria_" + perfil["bateria"], ups_kw * U["autonomia_min"] / 60,
        b["kg_kwh"], b["usd_kwh"], "baterias_" + perfil["bateria"])
    add("Energía", "genset", gross_kw * red, U["genset"]["kg_kw"], U["genset"]["usd_kw"],
        "gensets")
    t = U["transformador"]
    add("Energía", "transformador", gross_kw * red / t["fp"], t["kg_kva"], t["usd_kva"],
        "transformadores")
    for eq in perfil["refrigeracion"]:
        add("Refrigeración", eq, it_kw * red, U[eq]["kg_kw"], U[eq]["usd_kw"], "refrigeracion")
    return filas


SUBSISTEMA_CAPEX = {"servidores": "it", "almacenamiento": "it", "red": "it", "racks": "it",
                    "ups": "electrica", "baterias_plomo": "electrica",
                    "baterias_litio": "electrica", "gensets": "electrica",
                    "transformadores": "electrica", "refrigeracion": "mecanica"}


def reconciliar(caso: dict, fis: list[dict], par: dict) -> list[dict]:
    """US$ de la vía física vs US$ de la vía económica, por subsistema del capex."""
    perfil = par["perfiles"][caso["perfil"]]
    capex = mw_it(caso, par) * perfil["usd_mw"]
    usd_fis: dict[str, float] = defaultdict(float)
    for f in fis:
        usd_fis[SUBSISTEMA_CAPEX[f["familia"]]] += f["valor_usd_est"]
    tol = par.get("tolerancia_vias", 3.0)
    out = []
    for sub, share in perfil["capex_split"].items():
        eco = capex * share
        ratio = usd_fis.get(sub, 0.0) / eco if eco else None
        out.append({"subsistema_capex": sub, "usd_fisico": round(usd_fis.get(sub, 0.0)),
                    "usd_economico": round(eco),
                    "ratio_fis_eco": round(ratio, 2) if ratio else None,
                    "consistente": bool(ratio and 1 / tol <= ratio <= tol)})
    return out


# ---------------------------------------------------------------------------
# Observado (aduana)
# ---------------------------------------------------------------------------
def observado_por_familia(serie: dict, nac: list[dict], sa6: dict[str, dict],
                          ventana: tuple[int, int]) -> dict[str, tuple]:
    """{familia: (kg, usd)} importados en la ventana. Una familia sin ningún código con
    dato no es 'importación cero' (puede no estar en la nomenclatura): queda fuera."""
    sa6_de = {r["codigo_nacional"]: r["sa6"] for r in nac}
    acc: dict[str, list[float]] = defaultdict(lambda: [0.0, 0.0])
    for (c, a), s in serie.items():
        fam = sa6.get(sa6_de.get(c) or comun.sa6_de(c), {}).get("familia_mwbom")
        if fam and ventana[0] <= a <= ventana[1]:
            acc[fam][0] += s["kg"]
            acc[fam][1] += s["valor_usd"]
    return {k: tuple(v) for k, v in acc.items()}


def contraste(caso: dict, par: dict, vida: dict, obs: dict) -> list[dict]:
    """Esperado (BoM × reposición en la ventana) vs observado, por familia y escenario."""
    a0, a1 = caso["ventana"]
    w = a1 - a0 + 1
    out = []
    for esc in ESC_BOM:
        fam: dict[str, list[float]] = defaultdict(lambda: [0.0, 0.0])
        for f in bom_fisico(caso, esc, par):
            fam[f["familia"]][0] += f["masa_kg"]
            fam[f["familia"]][1] += f["valor_usd_est"]
        for familia, (kg, usd) in fam.items():
            tipo = par["tipo_vida"].get(familia)
            k = max(1.0, w / vida_media(vida, tipo, "central")) if tipo else 1.0
            okg, ousd = obs.get(familia, (None, None))
            hay = okg is not None and kg > 0
            out.append({"caso": caso["id"], "escenario_bom": esc, "familia": familia,
                        "esperado_kg": round(kg * k), "esperado_usd": round(usd * k),
                        "observado_kg": round(okg) if okg is not None else None,
                        "observado_usd": round(ousd) if ousd is not None else None,
                        "ratio_kg": round(okg / (kg * k), 3) if hay else None,
                        # auditoría de anuncios: MW que lo importado alcanzaría a equipar si
                        # TODO fuera a este caso (cota superior). En IA mirar US$, no kg.
                        "mw_equivalente_max_kg": round(caso["mw"] * okg / (kg * k), 1) if hay else None,
                        "mw_equivalente_max_usd": round(caso["mw"] * ousd / (usd * k), 1)
                        if hay and usd else None,
                        "ventana": f"{a0}-{a1}",
                        "estado_serie": "ok" if okg is not None else "sin_serie"})
    return out


# ---------------------------------------------------------------------------
# Factor de atribución
# ---------------------------------------------------------------------------
def atribucion(caso: dict, par: dict, vida: dict, masas: dict[str, dict],
               raee_it: dict[str, float], anio_raee: int, escenario_bom: str = "central"
               ) -> list[dict]:
    """f y RAEE_DC por escenario de vida. `masas`: salida de raee.masa_por_codigo;
    `raee_it`: {escenario: kg de RAEE IT limpio en anio_raee}."""
    a0, a1 = caso["ventana"]
    tot = sum(kg for d in masas.values() if d["serie"] == "limpia"
              for a, kg in d["masa"].items() if a0 <= a <= a1)
    anual = tot / (a1 - a0 + 1)
    stock: dict[str, float] = defaultdict(float)
    for f in bom_fisico(caso, escenario_bom, par):
        if f["familia"] in par["tipo_vida"]:
            stock[f["familia"]] += f["masa_kg"]
    out = []
    for esc in ESC_VIDA:
        flujo = sum(kg / vida_media(vida, par["tipo_vida"][fam], esc) for fam, kg in stock.items())
        f = flujo / anual if anual else None
        out.append({"caso": caso["id"], "escenario_vida": esc, "escenario_bom": escenario_bom,
                    "mw": caso["mw"], "base_mw": caso["base_mw"],
                    "stock_it_dc_kg": round(sum(stock.values())),
                    "flujo_it_dc_kg_anio": round(flujo),
                    "masa_it_importada_kg_anio": round(anual),
                    "f_atribucion": f, "anio_raee": anio_raee,
                    "raee_it_kg": raee_it[esc],
                    "raee_dc_kg": raee_it[esc] * f if f is not None else None,
                    "ventana": f"{a0}-{a1}", "confianza": "estimada"})
    return out


def casos(cfg: dict, par_mw: dict, inventario: list[dict] | None) -> list[dict]:
    """Casos a correr. Solo con MW de fuente (nunca inferidos)."""
    v = tuple(par_mw["ventana"])
    out = []
    ref = cfg.get("parque_referencia")
    if ref:
        out.append({"id": "parque_referencia", "mw": float(ref["mw"]),
                    "base_mw": "IT" if ref.get("base_mw") == "IT" else "bruta",
                    "perfil": "convencional", "ventana": v})
    if inventario:
        ops = [r for r in inventario if r.get("estado") == "operativo"
               and r.get("mayor_1mw") == "si" and comun.num(r.get("capacidad_mw"))]
        if ops:
            out.append({"id": "inventario_propio",
                        "mw": sum(comun.num(r["capacidad_mw"]) for r in ops),
                        "base_mw": "IT", "perfil": "convencional", "ventana": v,
                        "nota": "suma de MW tal como los declara cada fuente (base mixta)"})
        anio_fin = int(str(cfg["ultimo_periodo"])[:4])
        v_anuncio = tuple(cfg.get("ventana_anuncios") or (anio_fin - 1, anio_fin))
        for r in inventario:
            if r.get("tipo_uso") == "ia_escala_anunciado" and comun.num(r.get("capacidad_mw")):
                out.append({"id": f"anuncio: {r['nombre']}", "mw": comun.num(r["capacidad_mw"]),
                            "base_mw": "IT" if r.get("base_mw") == "IT" else "bruta",
                            "perfil": "ia", "ventana": v_anuncio})
    return out


def correr(cfg: dict, par: dict, aduana_res: dict | None = None,
           raee_res: dict | None = None) -> dict:
    from . import aduana, raee
    aduana_res = aduana_res or aduana.correr(cfg)
    raee_res = raee_res or raee.correr(cfg, par, aduana_res)
    sa6, nac = aduana.canasta(cfg)
    pm, vida = par["mwbom"], par["vida_util"]
    inv = comun.leer_csv(cfg["inventario"]) if cfg.get("inventario") else None
    comps, contr, recon, atr = [], [], [], []
    ref = raee_res["ultimo_anio"]
    fila = next(b for b in raee_res["banda"] if b["serie"] == "limpia" and b["anio"] == ref)
    raee_it = {e: fila[f"kg_{e}"] for e in ESC_VIDA}
    for caso in casos(cfg, pm, inv):
        obs = observado_por_familia(aduana_res["serie"], nac, sa6, caso["ventana"])
        for esc in ESC_BOM:
            fis = bom_fisico(caso, esc, pm)
            comps += [{"caso": caso["id"], "escenario_bom": esc, **f,
                       "unidades": round(f["unidades"], 1), "masa_kg": round(f["masa_kg"]),
                       "valor_usd_est": round(f["valor_usd_est"])} for f in fis]
            recon += [{"caso": caso["id"], "escenario_bom": esc, **r}
                      for r in reconciliar(caso, fis, pm)]
        contr += contraste(caso, pm, vida, obs)
        if caso["perfil"] == "convencional":
            atr += atribucion(caso, pm, vida, raee_res["masas"], raee_it, ref)
    return {"componentes": comps, "contraste": contr, "reconciliacion": recon,
            "atribucion": atr}


def main() -> None:
    a = comun.argumentos("MW -> equipo -> aduana y factor de atribución")
    cfg, par = comun.pais(a.pais), comun.parametros(a.parametros)
    r = correr(cfg, par)
    atr = [{**x, "f_atribucion": round(x["f_atribucion"], 4),
            "raee_dc_kg": round(x["raee_dc_kg"])} for x in r["atribucion"]]
    for nombre, filas in (("mwbom_componentes.csv", r["componentes"]),
                          ("mwbom_vs_aduana.csv", r["contraste"]),
                          ("mwbom_reconciliacion.csv", r["reconciliacion"]),
                          ("atribucion_dc.csv", atr)):
        print(comun.escribir_csv(comun.salida(nombre, cfg), filas))


if __name__ == "__main__":
    main()
