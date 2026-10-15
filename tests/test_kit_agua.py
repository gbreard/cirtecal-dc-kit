"""agua.py: directa sobre energía IT, indirecta sobre energía total, embalses aparte."""
import pytest

from kit import agua, comun


def _par():
    return comun.parametros()["agua"]


def test_directa_usa_it_e_indirecta_usa_total():
    pa = _par()
    e = {b: (100.0, 150.0) for b in agua.BANDA}            # GWh IT, GWh total
    intens = {b: {"sin_embalse": 1.0, "embalse": 10.0} for b in agua.BANDA}
    f = [x for x in agua.calcular("t", e, pa, "convencional", intens, "red")
         if x["refrigeracion"] == "evaporativo" and x["banda"] == "central"][0]
    wue = pa["wue_l_kwh_it"]["evaporativo"]["banda"][1]
    assert f["directa_hm3"] == pytest.approx(100e6 * wue / 1e9)
    assert f["indirecta_hm3"] == pytest.approx(150e6 * 1.0 / 1e9)
    assert f["indirecta_embalse_hm3"] == pytest.approx(150e6 * 10.0 / 1e9)
    assert f["total_hm3"] == pytest.approx(f["directa_hm3"] + f["indirecta_hm3"])


def test_matriz_y_bandas_ordenadas():
    i = agua.intensidad_matriz(_par(), comun.pais()["matriz_generacion"])
    assert i["bajo"]["sin_embalse"] < i["central"]["sin_embalse"] < i["alto"]["sin_embalse"]
    assert i["bajo"]["embalse"] < i["central"]["embalse"] < i["alto"]["embalse"]


def test_energia_del_parque_reproduce_a9():
    caso = next(c for c in comun.pais()["agua_casos"] if c["id"] == "parque_referencia")
    e = agua.energias(caso)
    assert round(e["bajo"][1]) == 364 and round(e["alto"][1]) == 561
