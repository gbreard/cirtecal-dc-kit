"""localizacion.py: distancias y clasificación."""
import pytest

from kit import comun, localizacion

CFG = {"nodo_principal": {"nombre": "N", "lat": 0.0, "lon": 0.0},
       "estaciones_amarre": [{"nombre": "E", "lat": 0.0, "lon": 1.0}],
       "region_principal": {"nucleo": ["Capital"], "con_umbral": ["Prov"]}}
PAR = {"umbral_nodo_km": 50.0, "region_principal_km": 60.0}


def test_haversine():
    assert comun.haversine_km((0, 0), (0, 1)) == pytest.approx(111.2, abs=0.1)
    assert comun.haversine_km((0, 0), (None, 1)) is None


def test_logica_y_region():
    inv = [{"nombre": "cerca", "provincia": "Prov", "lat": "0.1", "lon": "0"},
           {"nombre": "lejos", "provincia": "Prov", "lat": "2", "lon": "0"},
           {"nombre": "energia", "provincia": "Otra", "lat": "3", "lon": "0",
            "motivacion_energetica_fuente": "cita"},
           {"nombre": "sin coord", "provincia": "Capital"}]
    r = {f["nombre"]: f for f in localizacion.calcular(inv, CFG, PAR)}
    assert r["cerca"]["logica"] == "conectividad" and r["cerca"]["region_principal"] == "dentro"
    assert r["lejos"]["logica"] == "mixta" and r["lejos"]["region_principal"] == "fuera"
    assert r["energia"]["logica"] == "energia"
    assert r["sin coord"]["logica"] == "sin_dato" and r["sin coord"]["region_principal"] == "dentro"
