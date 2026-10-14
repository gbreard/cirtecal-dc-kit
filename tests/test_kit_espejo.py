"""espejo.py: clasificación de causas y descomposición, con datos sintéticos."""
from kit import comun, espejo

PE = comun.parametros()["espejo"]
U = espejo.umbrales(PE)
HUBS = {int(k) for k in PE["hubs_m49"]}


def test_causas_basicas():
    c = espejo.clasificar
    assert c(1, 10_000, 0, 1.0, U, HUBS)["causa"] == "inmaterial"
    assert c(1, 1e6, None, 1.0, U, HUBS)["causa"] == "sin_mapeo"
    assert c(344, 1e6, 1e4, 3.0, U, HUBS)["causa"] == "triangulacion_probable"
    assert c(1, 1e6, 1e4, 1.0, U, HUBS)["causa"] == "atribucion_probable"
    assert c(1, 1e6, 1e4, 2.5, U, HUBS)["causa"] == "secreto_probable"
    assert c(1, 1e6, 2e5, 2.5, U, HUBS)["causa"] == "secreto_dudoso"   # país 5×: zona gris
    assert c(1, 1.5e6, 1e6, 1.0, U, HUBS)["causa"] == "valuacion"
    assert c(1, 1e6, 1e6, 1.0, U, HUBS)["causa"] == "sin_brecha"


def test_cruce_y_cortes():
    esp = [{"sa6": "8473.30", "anio": 2023, "informante_m49": 842, "valor_fob_usd": 9e6},
           {"sa6": "8473.30", "anio": 2023, "informante_m49": 344, "valor_fob_usd": 2e6}]
    ad = [{"sa6": "8473.30", "anio": 2023, "origen": "EEUU", "valor_cif_usd": 6e5},
          {"sa6": "8473.30", "anio": 2023, "origen": "HK", "valor_cif_usd": 1e5}]
    mapa = {842: "EEUU", 344: "HK"}
    celdas = espejo.cruzar(esp, ad, mapa, U, HUBS)
    causas = {c["informante_m49"]: c["causa"] for c in celdas}
    assert causas == {842: "secreto_probable", 344: "triangulacion_probable"}
    estricto = espejo.umbrales(PE, **PE["cortes_sensibilidad"]["estricto"])
    c2 = {c["informante_m49"]: c["causa"] for c in espejo.cruzar(esp, ad, mapa, estricto, HUBS)}
    assert c2[842] == "secreto_dudoso"        # 15× no llega al corte estricto (20×)
    d = espejo.descomposicion(celdas, "base")
    assert {x["causa"]: x["brecha_usd"] for x in d}["secreto_probable"] == 8_400_000
