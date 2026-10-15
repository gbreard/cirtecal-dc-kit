"""Rendimientos por MW de IT: el cómputo métrico de un centro de datos.

Corre el modelo MW -> equipo de `mwbom.bom_fisico` (vía física) y `mwbom.reconciliar`
(vía económica) para 1 MW de IT, en los dos perfiles y los tres escenarios del BoM. No
agrega coeficientes propios: todo sale de config/parametros.yaml. Lo único que se
calcula acá son conversiones de unidades (kW -> TR) y el conteo de GPU (sistemas ×
GPU por sistema, que también está en parametros.yaml).

Cada fila lleva el estado de los parámetros que usa (verificado, parcial, supuesto o
no_declarado): el más débil de los que entran en la cantidad o capacidad, en la masa y en
el valor (`estado_cantidad`, `estado_masa`, `estado_valor`), el más débil de todos
(`estado`) y el detalle por parámetro (`estado_detalle`).

Salida: salidas/rendimientos_mw.csv (una fila por componente × perfil × escenario).
Uso:  python -m kit.rendimientos [--mw 1]
"""
from __future__ import annotations

from . import agua as _agua, comun, mwbom

KW_POR_TR = 3.517            # 1 tonelada de refrigeración = 3,517 kW térmicos
ORDEN = {"no_declarado": 0, "supuesto": 1, "parcial": 2, "verificado": 3}


def estado_unidad(texto: str, dim: str) -> str:
    """Estado de una dimensión (kg, kw, usd, gpus) leído del `_estado` de una unidad.
    "verificado kg/kW; usd supuesto" -> kg: verificado, usd: supuesto.
    Un estado sin dimensiones vale para todas; "verificado solo ..." se lee como parcial;
    una dimensión que el texto no menciona queda no_declarado."""
    s = (texto or "").lower().strip()
    if not s:
        return "no_declarado"
    general = None
    for parte in s.split(";"):
        pal = parte.split("(")[0].replace("/", " ").replace(",", " ").split()
        est = next((w for w in pal if w in ORDEN), None)     # "verificado kg" o "usd parcial"
        if est is None:
            continue
        if "solo" in parte:
            est = "parcial"
        dims = [d for d in pal if d in ("kg", "kw", "usd", "gpus", "kwh", "kva")]
        if not dims:
            general = est
        elif dim in dims or (dim == "kg" and any(d in ("kwh", "kva") for d in dims)):
            return est
    return general or "no_declarado"


def _peor(estados: dict[str, str]) -> str:
    return min(estados.values(), key=lambda e: ORDEN[e]) if estados else "no_declarado"


def _detalle(estados: dict[str, str]) -> str:
    return "; ".join(f"{k}={v}" for k, v in estados.items())


def _estado_texto(texto: str) -> str:
    """Primer estado que aparece en un `_estado` libre ("parcial (leído del gráfico)")."""
    pal = (texto or "").replace("(", " ").split()
    return next((w for w in pal if w in ORDEN), "no_declarado")


def tabla(par: dict, mw: float = 1.0, agua: dict | None = None,
          matriz: dict | None = None) -> list[dict]:
    """Filas de la tabla de rendimientos para `mw` MW de IT. Con `agua` (parametros.yaml)
    agrega el agua directa por escenario de refrigeración; con `matriz` (pais.yaml), también
    la indirecta de la red del país (sin embalses y evaporación de embalses, aparte)."""
    U, E = par["unidades"], par.get("_estado_parametros", {})
    filas = []

    def eu(nombre, *dims):
        return {f"{nombre}.{d}": estado_unidad(U[nombre].get("_estado", ""), d) for d in dims}

    def fila(perfil, esc, comp, familia, est, cantidad=None, unidad="", capacidad=None,
             unidad_cap="", masa_kg=None, usd=None, via="fisica", nota=""):
        # cantidad: sin los parámetros de masa (.kg) ni de precio (.usd); masa: sin precio;
        # valor: sin masa
        e_c = {k: v for k, v in est.items() if not k.endswith((".kg", ".usd"))}
        e_m = {k: v for k, v in est.items() if not k.endswith(".usd")}
        e_v = {k: v for k, v in est.items() if not k.endswith(".kg")}
        hay = {"c": cantidad is not None or capacidad is not None,
               "m": masa_kg is not None, "v": usd is not None}
        usados = {**(e_c if hay["c"] else {}), **(e_m if hay["m"] else {}),
                  **(e_v if hay["v"] else {})}
        filas.append({
            "perfil": perfil, "escenario": esc, "componente": comp, "familia": familia,
            "cantidad": None if cantidad is None else round(cantidad, 1), "unidad": unidad,
            "capacidad": None if capacidad is None else round(capacidad, 3),
            "unidad_capacidad": unidad_cap,
            "masa_t": None if masa_kg is None else round(masa_kg / 1000, 2),
            "valor_musd": None if usd is None else round(usd / 1e6, 2),
            "via": via, "estado": _peor(usados),
            "estado_cantidad": _peor(e_c) if hay["c"] else "",
            "estado_masa": _peor(e_m) if hay["m"] else "",
            "estado_valor": _peor(e_v) if hay["v"] else "",
            "estado_detalle": _detalle(usados), "nota": nota})

    for nombre_perfil, perfil in par["perfiles"].items():
        caso = {"id": f"{mw:g} MW IT", "mw": mw, "base_mw": "IT", "perfil": nombre_perfil}
        it_kw = mw * 1000
        tot_kw = it_kw * perfil["pue"]
        red = par["redundancia"][perfil["redundancia"]]
        e_rep = {"reparto_it": E.get("reparto_it", "no_declarado")}
        e_arq = {"arquitectura": E.get("arquitectura", "no_declarado")}
        e_red = {"redundancia": E.get("redundancia", "no_declarado")}
        e_pue = {"pue": E.get("pue", "no_declarado")}
        cs = E.get("capex_split", {})
        e_cs = {"capex_split": cs.get(nombre_perfil, "no_declarado") if isinstance(cs, dict) else cs}
        e_usdmw = {"usd_mw": E.get("usd_mw", "no_declarado")}
        for esc in mwbom.ESC_BOM:
            bom = {f["componente"]: f for f in mwbom.bom_fisico(caso, esc, par)}
            arq = perfil["arquitectura"][esc]
            sg = arq["servidor_gpu"]
            g = bom[sg]
            gpus = g["unidades"] * U[sg].get("gpus", 0) if U[sg].get("gpus") else None
            # --- IT ---------------------------------------------------------------
            fila(nombre_perfil, esc, "gpu", "servidores",
                 {**e_rep, **e_arq, **eu(sg, "kw", "gpus", "kg", "usd")},
                 gpus, "GPU", g["unidades"], f"sistemas {sg}", g["masa_kg"], g["valor_usd_est"],
                 nota=f"participación acelerada {arq['share_gpu']:.0%} de la potencia de servidores")
            c = bom["servidor_cpu"]
            fila(nombre_perfil, esc, "servidor_sin_acelerador", "servidores",
                 {**e_rep, **e_arq, **eu("servidor_cpu", "kw", "kg", "usd")},
                 c["unidades"], "servidores", masa_kg=c["masa_kg"], usd=c["valor_usd_est"])
            a = bom["almacenamiento"]
            fila(nombre_perfil, esc, "almacenamiento", "almacenamiento",
                 {**e_rep, **eu("almacenamiento", "kw", "kg", "usd")},
                 a["unidades"], "equipos", masa_kg=a["masa_kg"], usd=a["valor_usd_est"])
            s = bom["switch"]
            fila(nombre_perfil, esc, "conmutador", "red",
                 {**e_rep, **eu("switch", "kw", "kg", "usd")},
                 s["unidades"], "conmutadores", masa_kg=s["masa_kg"], usd=s["valor_usd_est"])
            r = bom["rack_vacio"]
            fila(nombre_perfil, esc, "rack", "racks",
                 {"kw_rack": E.get("kw_rack", "no_declarado"), **eu("rack_vacio", "kg", "usd")},
                 r["unidades"], "racks", perfil["kw_rack"][esc], "kW por rack",
                 r["masa_kg"], r["valor_usd_est"], nota="masa y valor del rack vacío")
            # subtotales por familia y total IT (sin racks: es la definición del Cuadro E.4)
            e_it = {}
            for fam, comps in (("servidores", ("servidor_cpu", sg)),
                               ("almacenamiento", ("almacenamiento",)), ("red", ("switch",))):
                est = {**e_rep, **(e_arq if fam == "servidores" else {})}
                for cc in comps:
                    est.update(eu(cc, "kg", "usd"))
                e_it.update(est)
                fila(nombre_perfil, esc, f"subtotal_{fam}", fam, est,
                     masa_kg=sum(bom[cc]["masa_kg"] for cc in comps),
                     usd=sum(bom[cc]["valor_usd_est"] for cc in comps))
            it_fams = [f for f in bom.values() if f["familia"] in par["tipo_vida"]]
            it_kg = sum(f["masa_kg"] for f in it_fams)
            it_usd = sum(f["valor_usd_est"] for f in it_fams)
            fila(nombre_perfil, esc, "total_it", "it", e_it, masa_kg=it_kg, usd=it_usd,
                 nota="servidores + almacenamiento + red, sin racks (definición del Cuadro E.4)")
            fila(nombre_perfil, esc, "total_it_con_racks", "it",
                 {**e_it, **eu("rack_vacio", "kg", "usd")},
                 masa_kg=it_kg + r["masa_kg"], usd=it_usd + r["valor_usd_est"])
            # --- Potencia y calor ---------------------------------------------------
            fila(nombre_perfil, esc, "potencia_total", "energia", e_pue,
                 capacidad=tot_kw / 1000, unidad_cap="MW", nota=f"IT × PUE {perfil['pue']}")
            fila(nombre_perfil, esc, "calor_a_evacuar", "refrigeracion", {"fisica": "verificado"},
                 it_kw / KW_POR_TR, "TR", it_kw / 1000, "MW térmicos",
                 nota="toda la potencia de IT se vuelve calor; 1 TR = 3,517 kW")
            # --- Agua (kit.agua, operación continua) -----------------------------------
            if agua:
                i = mwbom.ESC_BOM.index(esc)
                e = {b: (mw * _agua.HORAS / 1000, mw * _agua.HORAS / 1000 * perfil["pue"])
                     for b in _agua.BANDA}
                intens = _agua.intensidad_matriz(agua, matriz) if matriz else None
                nulo = {b: {"sin_embalse": 0.0, "embalse": 0.0} for b in _agua.BANDA}
                for x in _agua.calcular("", e, agua, nombre_perfil, intens or nulo, "red"):
                    if x["banda"] != esc:
                        continue
                    tec = x["tecnologia_refrigeracion"]
                    fila(nombre_perfil, esc, f"agua_directa_{x['refrigeracion']}", "agua",
                         {f"wue.{tec}": _estado_texto(agua["wue_l_kwh_it"][tec].get("_estado"))},
                         x["directa_hm3"] * 1e6, "m³/año", x["wue_l_kwh_it"], "L/kWh IT",
                         nota=f"directa = energía IT × WUE ({tec}); banda {esc}")
                if intens:
                    gen = agua["generacion_l_kwh"]
                    est = {f"generacion.{k}": _estado_texto(gen.get(k, gen["hidro"]).get("_estado"))
                           for k in matriz["gwh"] if k in gen
                           and not gen[k].get("_estado", "").startswith("sin_dato")}
                    est["pue"] = E.get("pue", "no_declarado")
                    tot_kwh = e[esc][1] * 1e6
                    fila(nombre_perfil, esc, "agua_indirecta_red", "agua", est,
                         tot_kwh * intens[esc]["sin_embalse"] / 1000, "m³/año",
                         intens[esc]["sin_embalse"], "L/kWh total",
                         nota=f"energía total × intensidad de la matriz {matriz.get('anio')} "
                              "sin embalses (turbina de gas y motores: sin dato, 0)")
                    fila(nombre_perfil, esc, "agua_indirecta_embalse", "agua",
                         {"generacion.hidro": _estado_texto(gen["hidro"].get("_estado")),
                          "pue": E.get("pue", "no_declarado")},
                         tot_kwh * intens[esc]["embalse"] / 1000, "m³/año",
                         intens[esc]["embalse"], "L/kWh total",
                         nota="evaporación de embalses asignada a la hidro: se informa aparte")
            # --- Infraestructura ----------------------------------------------------
            infra_kg, infra_est = 0.0, {}
            for eq in perfil["refrigeracion"]:
                f = bom[eq]
                est = {**e_red, **eu(eq, "kg", "usd")}
                fila(nombre_perfil, esc, f"enfriamiento_{eq}", "refrigeracion", est,
                     f["unidades"] / KW_POR_TR, "TR", f["unidades"] / 1000, "MW",
                     f["masa_kg"], f["valor_usd_est"], nota="IT × redundancia")
                infra_kg += f["masa_kg"]; infra_est.update(est)
            f = bom["ups"]
            est = {**e_red, **eu("ups", "kg", "usd")}
            fila(nombre_perfil, esc, "ups", "ups", est, capacidad=f["unidades"] / 1000,
                 unidad_cap="MW", masa_kg=f["masa_kg"], usd=f["valor_usd_est"],
                 nota="IT × redundancia")
            infra_kg += f["masa_kg"]; infra_est.update(est)
            nb = "bateria_" + perfil["bateria"]
            f = bom[nb]
            est = {**e_red, "autonomia_min": E.get("autonomia_min", "no_declarado"),
                   **eu(nb, "kg", "usd")}
            fila(nombre_perfil, esc, f"baterias_{perfil['bateria']}", "baterias", est,
                 capacidad=f["unidades"], unidad_cap="kWh", masa_kg=f["masa_kg"],
                 usd=f["valor_usd_est"], nota=f"UPS × {U['autonomia_min']} min")
            infra_kg += f["masa_kg"]; infra_est.update(est)
            f = bom["genset"]
            est = {**e_pue, **e_red, **eu("genset", "kg", "usd")}
            fila(nombre_perfil, esc, "grupo_electrogeno", "gensets", est,
                 capacidad=f["unidades"] / 1000, unidad_cap="MW", masa_kg=f["masa_kg"],
                 usd=f["valor_usd_est"], nota="total × redundancia")
            infra_kg += f["masa_kg"]; infra_est.update(est)
            f = bom["transformador"]
            est = {**e_pue, **e_red, **eu("transformador", "kg", "usd")}
            fila(nombre_perfil, esc, "transformador", "transformadores", est,
                 capacidad=f["unidades"] / 1000, unidad_cap="MVA", masa_kg=f["masa_kg"],
                 usd=f["valor_usd_est"], nota="total / fp × redundancia")
            infra_kg += f["masa_kg"]; infra_est.update(est)
            fila(nombre_perfil, esc, "total_infraestructura", "infraestructura", infra_est,
                 masa_kg=infra_kg, nota="refrigeración + UPS + baterías + grupos + transformadores")
            # --- Inversión ----------------------------------------------------------
            capex = mw * perfil["usd_mw"]
            share_it = perfil["capex_split"].get("it")
            if share_it is None:
                # usd_mw es la obra sin IT; el IT sale de la vía física
                fila(nombre_perfil, esc, "inversion_obra_sin_it", "inversion", e_usdmw,
                     usd=capex, via="economica")
                fila(nombre_perfil, esc, "inversion_it", "inversion", e_it, usd=it_usd,
                     via="fisica")
                fila(nombre_perfil, esc, "inversion_total", "inversion", {**e_usdmw, **e_it},
                     usd=capex + it_usd, via="economica+fisica")
            else:
                # usd_mw incluye el IT; se reparte con capex_split
                fila(nombre_perfil, esc, "inversion_obra_sin_it", "inversion",
                     {**e_usdmw, **e_cs}, usd=capex * (1 - share_it), via="economica")
                fila(nombre_perfil, esc, "inversion_it", "inversion", {**e_usdmw, **e_cs},
                     usd=capex * share_it, via="economica")
                fila(nombre_perfil, esc, "inversion_it", "inversion", e_it, usd=it_usd,
                     via="fisica", nota="contraste con la vía económica")
                fila(nombre_perfil, esc, "inversion_total", "inversion", e_usdmw, usd=capex,
                     via="economica")
            for rr in mwbom.reconciliar(caso, list(bom.values()), par):
                fila(nombre_perfil, esc, f"reconciliacion_{rr['subsistema_capex']}", "inversion",
                     {**e_usdmw, **e_cs}, capacidad=rr["ratio_fis_eco"],
                     unidad_cap="física / económica", usd=rr["usd_fisico"], via="fisica",
                     nota=f"económica US$ {rr['usd_economico'] / 1e6:.2f} M; "
                          f"{'consistente' if rr['consistente'] else 'FUERA de tolerancia'}")
    return filas


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description="Rendimientos por MW de IT")
    ap.add_argument("--pais", default="config/pais.yaml")
    ap.add_argument("--parametros", default="config/parametros.yaml")
    ap.add_argument("--mw", type=float, default=1.0, help="MW de IT (default 1)")
    a = ap.parse_args()
    cfg, par = comun.pais(a.pais), comun.parametros(a.parametros)
    print(comun.escribir_csv(comun.salida("rendimientos_mw.csv", cfg), tabla(par["mwbom"], a.mw, par.get("agua"),
                                                   cfg.get("matriz_generacion"))))


if __name__ == "__main__":
    main()
