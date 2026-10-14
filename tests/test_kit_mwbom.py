"""mwbom.py con parámetros del kit y datos sintéticos."""
import pytest

from kit import comun, mwbom

PAR = comun.parametros()


def _caso(mw=10.0, base="IT"):
    return {"id": "t", "mw": mw, "base_mw": base, "perfil": "convencional",
            "ventana": (2016, 2025)}


def _masas(kg_anio=1_000_000.0):
    return {"X": {"sa6": "8471.50", "tipo_vida": "computo", "serie": "limpia",
                  "masa": {a: kg_anio for a in range(2016, 2026)}}}


def test_f_lineal_en_mw_y_bruta_divide_por_pue():
    rit = {"corto": 1.0, "central": 1.0, "largo": 1.0}
    f10 = mwbom.atribucion(_caso(10), PAR["mwbom"], PAR["vida_util"], _masas(), rit, 2026)[1]
    f20 = mwbom.atribucion(_caso(20), PAR["mwbom"], PAR["vida_util"], _masas(), rit, 2026)[1]
    assert f20["f_atribucion"] == pytest.approx(2 * f10["f_atribucion"])
    pue = PAR["mwbom"]["perfiles"]["convencional"]["pue"]
    fb = mwbom.atribucion(_caso(10 * pue, "bruta"), PAR["mwbom"], PAR["vida_util"], _masas(),
                          rit, 2026)[1]
    assert fb["f_atribucion"] == pytest.approx(f10["f_atribucion"])


def test_vida_mas_corta_da_f_mayor():
    rit = {"corto": 1.0, "central": 1.0, "largo": 1.0}
    r = {x["escenario_vida"]: x["f_atribucion"] for x in
         mwbom.atribucion(_caso(), PAR["mwbom"], PAR["vida_util"], _masas(), rit, 2026)}
    assert r["corto"] > r["central"] > r["largo"]


def test_contraste_sin_serie_no_es_cero():
    """Borde: una familia sin código con dato queda 'sin_serie', no con observado 0."""
    filas = mwbom.contraste(_caso(), PAR["mwbom"], PAR["vida_util"], {})
    assert all(f["estado_serie"] == "sin_serie" and f["observado_kg"] is None for f in filas)


def test_reconciliacion_marca_supuesto_roto():
    fis = mwbom.bom_fisico(_caso(), "central", PAR["mwbom"])
    rec = mwbom.reconciliar(_caso(), fis, PAR["mwbom"])
    assert {r["subsistema_capex"] for r in rec} == {"electrica", "mecanica"}
    assert all(isinstance(r["consistente"], bool) for r in rec)
