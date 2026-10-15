"""rendimientos.py: tabla por MW de IT sobre el modelo de mwbom (sin red)."""
from kit import comun, rendimientos


def _tabla(mw=1.0):
    return rendimientos.tabla(comun.parametros()["mwbom"], mw)


def test_reproduce_cuadro_e4():
    # parque de referencia: 32 MW IT, convencional, central -> masa IT 2.122 t, US$ 875 M
    f = next(x for x in _tabla(32.0) if x["perfil"] == "convencional"
             and x["escenario"] == "central" and x["componente"] == "total_it")
    assert round(f["masa_t"]) == 2122 and round(f["valor_musd"]) == 875


def test_banda_y_estado_en_cada_fila():
    filas = _tabla()
    claves = {(x["componente"], x["via"]) for x in filas}
    for comp, via in claves:
        for perfil in ("convencional", "ia"):
            esc = {x["escenario"] for x in filas if x["componente"] == comp
                   and x["via"] == via and x["perfil"] == perfil}
            assert esc in (set(), {"bajo", "central", "alto"}), (comp, perfil)
    assert all(x["estado"] in rendimientos.ORDEN for x in filas)


def test_estado_por_dimension():
    e = rendimientos.estado_unidad
    assert e("verificado kW/kg/gpus; usd parcial", "usd") == "parcial"
    assert e("verificado kW/kg/gpus; usd parcial", "gpus") == "verificado"
    assert e("verificado kg", "usd") == "no_declarado"
    assert e("verificado solo unidades chicas", "kg") == "parcial"
