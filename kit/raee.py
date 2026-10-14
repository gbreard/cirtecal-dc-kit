"""RAEE estimado desde la masa importada: modelo de cohortes con rezago, bandas por
escenario de vida útil y variante con segunda vida.

    R(t) = Σ_k  M(t−k) · r(k),   Σ r(k) = 1

M = kg importados por código; r(k) = fracción que se RETIRA DEL PRIMER USO a los k años.
Se corre por código y recién después se agrega por serie (nunca al revés: cada código
tiene su vida útil). Tres escenarios de vida (corto / central / largo): el resultado es
una banda, nunca un punto.

Qué es r(k): el retiro del primer uso. El modelo base lo trata como descarte en el mismo
año (variante A). La variante B manda una fracción q a segunda vida durante d años antes
del descarte: RAEE(t) = (1−q)·R(t) + q·R(t−d). Lo que se reacondiciona DESPUÉS de haber
sido residuo no se descuenta (ya es RAEE generado). Ojo: el escenario largo (7–10 años)
ya incluye reúso; aplicarle B cuenta dos veces la segunda vida.

Discretización anual: k es la diferencia en años calendario entre importación y retiro;
toda la masa de la cohorte t−k que se retira a la edad k sale en el año t (equivale a
importación y retiro a mitad de año).

Series (columna `serie_raee` de la canasta SA6):
  limpia         equipamiento IT atribuible (titular)
  cota_superior  partes y genéricos no aislables
  baterias       régimen propio y doble uso (automotor, solar): nunca se suma al titular

Salidas en `salidas/`: raee_serie_codigo.csv, raee_banda.csv, raee_segunda_vida.csv,
raee_sanity.csv.  Uso:  python -m kit.raee
"""
from __future__ import annotations

from collections import defaultdict

from . import comun

ESCENARIOS = ("corto", "central", "largo")
SERIES = ("limpia", "cota_superior", "baterias")


# ---------------------------------------------------------------------------
# Distribución de retiros
# ---------------------------------------------------------------------------
def r_uniforme(a: int, b: int) -> dict[int, float]:
    """Peso 1/(b−a+1) en cada entero de [a, b]. Media (a+b)/2. Default reportable."""
    n = b - a + 1
    return {k: 1.0 / n for k in range(a, b + 1)}


def r_triangular(a: int, b: int) -> dict[int, float]:
    """Triangular simétrica de igual media: peso ∝ h − |k − c|, c = (a+b)/2,
    h = (b−a)/2 + 1 (triángulo de soporte (a−1, b+1) evaluado en a…b). Sensibilidad."""
    c = (a + b) / 2
    w = {k: (b - a) / 2 + 1 - abs(k - c) for k in range(a, b + 1)}
    s = sum(w.values())
    return {k: v / s for k, v in w.items()}


DISTRIBUCIONES = {"uniforme": r_uniforme, "triangular": r_triangular}


def vida_media(vida: dict, tipo: str, escenario: str) -> float:
    """Vida media (años) de un tipo en un escenario. La usa también mwbom (mismo parámetro)."""
    a, b = vida[tipo][escenario]
    return (a + b) / 2


def cohortes(masa: dict[int, float], r: dict[int, float], hasta: int) -> dict[int, float]:
    """R(t) para t en [primer año de la serie, hasta]. Cohortes anteriores al inicio de la
    serie aportan 0: no se imputa un stock que no se observa (subestima los primeros años)."""
    if not masa:
        return {}
    return {t: sum(masa.get(t - k, 0.0) * p for k, p in r.items())
            for t in range(min(masa), hasta + 1)}


# ---------------------------------------------------------------------------
# Insumo: masa por código
# ---------------------------------------------------------------------------
def masa_por_codigo(serie: dict[tuple[str, int], dict], nac: list[dict],
                    sa6: dict[str, dict], excluir: frozenset = frozenset()
                    ) -> dict[str, dict]:
    """{código: {'sa6', 'tipo_vida', 'serie', 'masa': {año: kg}}} para los códigos cuya SA6
    tiene serie RAEE. Celdas sin peso ya vienen fuera (no se imputan). `excluir`: códigos
    que se sacan para una sensibilidad (p. ej. la serie sin empalme)."""
    sa6_de = {r["codigo_nacional"]: r["sa6"] for r in nac}
    out: dict[str, dict] = {}
    for (c, a), s in serie.items():
        if c in excluir:
            continue
        meta = sa6.get(sa6_de.get(c) or comun.sa6_de(c), {})
        if not meta.get("serie_raee"):
            continue
        d = out.setdefault(c, {"sa6": meta["sa6"], "tipo_vida": meta["tipo_vida"],
                               "serie": meta["serie_raee"], "masa": {}})
        if s.get("celdas_sin_kg", 0) < s.get("celdas", 1):     # al menos una celda con peso
            d["masa"][a] = d["masa"].get(a, 0.0) + s["kg"]
    return out


# ---------------------------------------------------------------------------
# Estimación
# ---------------------------------------------------------------------------
def estimar(masas: dict[str, dict], vida: dict, hasta: int, ultimo_anio: int,
            inicio_canasta: int, distribucion: str = "uniforme") -> list[dict]:
    """Filas por (año, escenario, código)."""
    r_de = DISTRIBUCIONES[distribucion]
    filas = []
    for c, d in sorted(masas.items()):
        for esc in ESCENARIOS:
            a, b = vida[d["tipo_vida"]][esc]
            for t, kg in cohortes(d["masa"], r_de(a, b), hasta).items():
                filas.append({"anio": t, "escenario": esc, "codigo": c, "sa6": d["sa6"],
                              "tipo_vida": d["tipo_vida"], "serie": d["serie"],
                              "kg_raee": kg,
                              "horizonte": "historico" if t <= ultimo_anio else "comprometido",
                              # la ventana [t−b, t−a] toca años previos a la canasta completa
                              "cohortes_completas": int(t - b >= inicio_canasta)})
    return filas


def por_serie(filas: list[dict]) -> dict[tuple[str, str, int], float]:
    """{(serie, escenario, año): kg}."""
    acc: dict[tuple, float] = defaultdict(float)
    for f in filas:
        acc[(f["serie"], f["escenario"], f["anio"])] += f["kg_raee"]
    return dict(acc)


def banda(filas: list[dict]) -> list[dict]:
    """Por (serie, año): corto, central, largo, mínimo y máximo de los tres."""
    acc = por_serie(filas)
    meta: dict[tuple, dict] = {}
    for f in filas:
        m = meta.setdefault((f["serie"], f["anio"]),
                            {"horizonte": f["horizonte"], "cohortes_completas": 1})
        m["cohortes_completas"] &= f["cohortes_completas"]
    out = []
    for (serie, anio) in sorted(meta, key=lambda k: (SERIES.index(k[0]), k[1])):
        v = {e: acc.get((serie, e, anio), 0.0) for e in ESCENARIOS}
        out.append({"serie": serie, "anio": anio, "kg_min": round(min(v.values()), 1),
                    "kg_central": round(v["central"], 1), "kg_max": round(max(v.values()), 1),
                    "kg_corto": round(v["corto"], 1), "kg_largo": round(v["largo"], 1),
                    **meta[(serie, anio)]})
    return out


# ---------------------------------------------------------------------------
# Segunda vida (variante B)
# ---------------------------------------------------------------------------
def segunda_vida(R: dict[int, float], q: float, d: int, hasta: int) -> dict:
    """Lo que se retira en t: (1−q) se descarta en t, q se descarta en t+d.
    Balance al cierre de `hasta`: Σ R(t≤hasta) = Σ RAEE(t≤hasta) + masa en segunda vida,
    y esa masa se descarta entera en hasta+1 … hasta+d."""
    raee = {t: (1 - q) * R[t] + q * R.get(t - d, 0.0) for t in R if t <= hasta}
    stock = q * sum(R.get(s, 0.0) for s in range(hasta - d + 1, hasta + 1))
    posterior = {hasta + j: q * R.get(hasta + j - d, 0.0) for j in range(1, d + 1)}
    return {"raee": raee, "stock_cierre": stock, "descarte_posterior": posterior}


def tabla_segunda_vida(filas: list[dict], qs, ds, anio_ref: int, periodo: tuple[int, int],
                       f: dict[str, float] | None = None) -> list[dict]:
    """Retiros, RAEE y masa en segunda vida al cierre del período (serie limpia), por
    escenario, q y d. Con `f` (factor de atribución por escenario) agrega el nivel DC,
    con f FIJO dentro de cada comparación A/B."""
    acc = por_serie(filas)
    a0, a1 = periodo
    out = []
    for esc in ESCENARIOS:
        R = {t: kg for (s, e, t), kg in acc.items() if s == "limpia" and e == esc}
        for d in ds:
            for q in qs:
                sv = segunda_vida(R, q, d, a1)
                niveles = [("nacional", 1.0)] + ([("dc", f[esc])] if f else [])
                for nivel, k in niveles:
                    out.append({
                        "escenario": esc, "variante": "A" if q == 0 else "B", "q": q,
                        "d_anios": d, "nivel": nivel, "factor": k,
                        f"retiros_{anio_ref}_kg": k * R.get(anio_ref, 0.0),
                        f"retiros_{a0}_{a1}_kg": k * sum(R.get(t, 0.0) for t in range(a0, a1 + 1)),
                        f"raee_{anio_ref}_kg": k * sv["raee"].get(anio_ref, 0.0),
                        f"raee_{a0}_{a1}_kg": k * sum(sv["raee"].get(t, 0.0)
                                                      for t in range(a0, a1 + 1)),
                        f"segunda_vida_cierre_{a1}_kg": k * sv["stock_cierre"],
                        "balance_kg": k * (sum(v for t, v in R.items() if t <= a1)
                                           - sum(sv["raee"].values()) - sv["stock_cierre"])})
    return out


def sanity(bnd: list[dict], cfg: dict) -> dict | None:
    """RAEE IT (limpia, central) como % del e-waste nacional. Chequeo de MAGNITUD: no
    calibra ningún parámetro. Necesita ewaste_kg_hab, ewaste_anio y poblacion en pais.yaml."""
    if not all(k in cfg for k in ("ewaste_kg_hab", "ewaste_anio", "poblacion")):
        return None
    total = cfg["ewaste_kg_hab"] * cfg["poblacion"]
    lim = next((f["kg_central"] for f in bnd if f["serie"] == "limpia"
                and f["anio"] == cfg["ewaste_anio"]), 0.0)
    return {"anio": cfg["ewaste_anio"], "ewaste_pais_kg": round(total),
            "raee_it_limpia_kg": lim, "pct": round(100 * lim / total, 3),
            "plausible": lim < 0.10 * total}


# ---------------------------------------------------------------------------
def correr(cfg: dict, par: dict, aduana_res: dict | None = None,
           excluir: frozenset = frozenset(), distribucion: str | None = None) -> dict:
    from . import aduana
    aduana_res = aduana_res or aduana.correr(cfg)
    sa6, nac = aduana.canasta(cfg)
    pr = par["raee"]
    ultimo = int(str(cfg["ultimo_periodo"])[:4])
    masas = masa_por_codigo(aduana_res["serie"], nac, sa6, excluir)
    filas = estimar(masas, par["vida_util"], pr["anio_proyeccion_max"], ultimo,
                    pr["anio_inicio_canasta"], distribucion or pr["distribucion"])
    return {"filas": filas, "banda": banda(filas), "masas": masas, "ultimo_anio": ultimo}


def main() -> None:
    a = comun.argumentos("RAEE por cohortes (banda y segunda vida)")
    cfg, par = comun.pais(a.pais), comun.parametros(a.parametros)
    from . import aduana, mwbom
    ad = aduana.correr(cfg)
    r = correr(cfg, par, ad)
    pr = par["raee"]
    # con parque de referencia se agrega el nivel data center (f fijo por escenario)
    f = {x["escenario_vida"]: x["f_atribucion"]
         for x in mwbom.correr(cfg, par, ad, r)["atribucion"]
         if x["caso"] == "parque_referencia"} or None
    sv = tabla_segunda_vida(r["filas"], pr["segunda_vida"]["q"], pr["segunda_vida"]["d"],
                            r["ultimo_anio"], (r["ultimo_anio"] + 1, pr["anio_proyeccion_max"]),
                            f)
    for nombre, filas in (("raee_serie_codigo.csv", [{**f, "kg_raee": round(f["kg_raee"], 1)}
                                                      for f in r["filas"]]),
                          ("raee_banda.csv", r["banda"]),
                          ("raee_segunda_vida.csv", [{k: round(v, 1) if k.endswith("_kg") else v
                                                      for k, v in x.items()} for x in sv])):
        print(comun.escribir_csv(comun.salida(nombre, cfg), filas))
    s = sanity(r["banda"], cfg)
    if s:
        print(comun.escribir_csv(comun.salida("raee_sanity.csv", cfg), [s]))


if __name__ == "__main__":
    main()
