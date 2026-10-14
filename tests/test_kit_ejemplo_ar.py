"""Corre el ejemplo argentino de punta a punta (sin red) y reproduce las cifras
publicadas: f = 0,163 · RAEE DC 2026 = 503 t · RAEE DC 2027–2030 = 1.501 t.

Sobre 503 vs 504 t (2026) y 1.500 vs 1.501 t (2027–2030): las dos parejas salen del mismo
modelo; cambia solo el redondeo de f. Con f sin redondear (0,16256) da 503 t y 1.500 t;
con f redondeado a 4 decimales (0,1626) da 504 t y 1.501 t. La cifra publicada de 2026
(503 t) usa f sin redondear; la de 2027–2030 (1.501 t) usó f redondeado. El test
reproduce las dos y las deja explícitas.
"""
import pytest

from kit import aduana, comun, inventario, localizacion, mwbom, raee

CFG, PAR = comun.pais(), comun.parametros()


@pytest.fixture(scope="module")
def corrida():
    ad = aduana.correr(CFG)
    rr = raee.correr(CFG, PAR, ad)
    mw = mwbom.correr(CFG, PAR, ad, rr)
    atr = {x["escenario_vida"]: x for x in mw["atribucion"] if x["caso"] == "parque_referencia"}
    return ad, rr, atr


def test_f_y_raee_dc_2026(corrida):
    _, _, atr = corrida
    assert round(atr["central"]["f_atribucion"], 3) == 0.163
    assert round(atr["central"]["raee_dc_kg"] / 1000) == 503
    assert round(atr["corto"]["raee_dc_kg"] / 1000) == 573      # banda publicada 321–573
    assert round(atr["largo"]["raee_dc_kg"] / 1000) == 321


def test_raee_dc_2027_2030(corrida):
    _, rr, atr = corrida
    acc = raee.por_serie(rr["filas"])
    w = sum(acc[("limpia", "central", a)] for a in range(2027, 2031))
    f = atr["central"]["f_atribucion"]
    assert round(w / 1000) == 9228
    assert round(w * round(f, 4) / 1000) == 1501               # convención publicada
    assert round(w * f / 1000) == 1500                          # f sin redondear


def test_banda_igual_a_la_publicada(corrida):
    _, rr, _ = corrida
    pub = {(r["serie"], int(r["anio"])): r for r in
           comun.leer_csv("ejemplo_ar/publicado_raee_estimado_banda.csv")}
    for b in rr["banda"]:
        p = pub[(b["serie"], b["anio"])]
        for k in ("kg_min", "kg_central", "kg_max"):
            assert b[k] == pytest.approx(float(p[k]), abs=1.0)


def test_inventario_v13():
    inv = comun.leer_csv(CFG["inventario"])
    assert not [p for p in inventario.validar(inv, CFG["inventario_reglas"])
                if p["nivel"] == "error"]
    m = inventario.metricas(inv, CFG["parque_referencia"])
    assert (m["registros"], m["operativos"], m["conteo_base"]) == (41, 33, 39)
    assert (m["comparables_referencia"], m["mw_it"], m["cobertura_mw_it"]) == (3, 7.6, 0.237)


def test_localizacion_igual_al_inventario():
    inv = comun.leer_csv(CFG["inventario"])
    loc = localizacion.calcular(inv, CFG, PAR["localizacion"])
    for r, l in zip(inv, loc):
        assert r["logica"] == l["logica"]
        if r["dist_ixp_principal_km"]:
            assert l["dist_nodo_principal_km"] == pytest.approx(float(r["dist_ixp_principal_km"]),
                                                               abs=0.15)
