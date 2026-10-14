"""raee.py sin datos de ningún país: distribuciones, cohortes, banda y segunda vida."""
import pytest

from kit import raee

VIDA = {"computo": {"corto": [3, 4], "central": [4, 6], "largo": [6, 9]}}


@pytest.mark.parametrize("a,b", [(3, 4), (4, 6), (6, 9), (7, 10), (5, 5)])
def test_distribuciones_suman_uno_y_misma_media(a, b):
    u, t = raee.r_uniforme(a, b), raee.r_triangular(a, b)
    assert sum(u.values()) == pytest.approx(1) and sum(t.values()) == pytest.approx(1)
    mu = sum(k * p for k, p in u.items())
    assert mu == pytest.approx((a + b) / 2)
    assert sum(k * p for k, p in t.items()) == pytest.approx(mu)
    var = lambda r: sum((k - mu) ** 2 * p for k, p in r.items())
    assert var(t) <= var(u) + 1e-12


def test_conservacion_de_masa_con_horizonte_largo():
    masa = {2010: 1000.0, 2012: 500.0}
    R = raee.cohortes(masa, raee.r_uniforme(4, 6), 2030)
    assert sum(R.values()) == pytest.approx(1500.0)


def test_sin_cohortes_previas_a_la_serie():
    """Borde: los primeros años no reciben retiros de cohortes no observadas."""
    R = raee.cohortes({2010: 1000.0}, raee.r_uniforme(4, 6), 2020)
    assert all(R[t] == 0 for t in range(2010, 2014))
    assert R[2014] == pytest.approx(1000 / 3)


def test_estimar_y_banda_corto_adelanta():
    masas = {"X": {"sa6": "8471.50", "tipo_vida": "computo", "serie": "limpia",
                   "masa": {2010: 900.0}}}
    filas = raee.estimar(masas, VIDA, 2030, 2020, 2007)
    b = {f["anio"]: f for f in raee.banda(filas)}
    assert b[2013]["kg_corto"] > 0 and b[2013]["kg_largo"] == 0
    assert b[2013]["horizonte"] == "historico" and b[2025]["horizonte"] == "comprometido"


@pytest.mark.parametrize("q,d", [(0.25, 1), (0.5, 2), (0.5, 3)])
def test_segunda_vida_balance_hasta_el_descarte(q, d):
    R = {t: float(t - 2000) for t in range(2010, 2031)}
    sv = raee.segunda_vida(R, q, d, 2030)
    assert sum(R.values()) == pytest.approx(sum(sv["raee"].values()) + sv["stock_cierre"])
    assert sum(sv["descarte_posterior"].values()) == pytest.approx(sv["stock_cierre"])


def test_segunda_vida_q0_es_variante_a():
    R = {2024: 10.0, 2025: 20.0}
    sv = raee.segunda_vida(R, 0.0, 2, 2025)
    assert sv["raee"] == R and sv["stock_cierre"] == 0


def test_masa_no_imputa_celdas_sin_peso():
    serie = {("A", 2010): {"kg": 0.0, "celdas": 1, "celdas_sin_kg": 1},
             ("A", 2011): {"kg": 5.0, "celdas": 2, "celdas_sin_kg": 1}}
    nac = [{"codigo_nacional": "A", "sa6": "8471.50"}]
    sa6 = {"8471.50": {"sa6": "8471.50", "tipo_vida": "computo", "serie_raee": "limpia"}}
    m = raee.masa_por_codigo(serie, nac, sa6)
    assert m["A"]["masa"] == {2011: 5.0}
