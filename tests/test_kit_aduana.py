"""aduana.py: empalme, control de códigos vacíos y deflactor (sin red)."""
import pytest

from kit import aduana
from kit.fuentes.aduana_plantilla import Registro


def test_empalme_en_cadena():
    assert aduana.empalmar("A", {"A": "B", "B": "C"}) == "C"
    assert aduana.empalmar("Z", {"A": "B"}) == "Z"


def test_empalme_parcial():
    # 8471.70.90 sigue vigente y una parte pasó a 8471.70.40 (SSD): el nuevo se lee con el viejo
    suc = {"8471.70.90": "ex 8471.70.40", "8471.70.12": "8471.70.10"}
    assert aduana.empalmar("8471.70.40", suc) == "8471.70.90"
    assert aduana.empalmar("8471.70.90", suc) == "8471.70.90"
    assert aduana.empalmar("8471.70.12", suc) == "8471.70.10"
    serie = {("8471.70.90", a): {} for a in range(2002, 2026)}
    serie.update({("8471.70.40", a): {} for a in (2024, 2025)})
    ctrl = {c["codigo"]: c["marcas"] for c in aduana.control_codigos(
        serie, ["8471.70.90", "8471.70.40"], (2002, 2025), {"SA2022": 2024}, suc)}
    assert ctrl == {"8471.70.90": "ok", "8471.70.40": "nace_en_enmienda"}


def test_control_codigos():
    serie = {("viejo", a): {} for a in range(2002, 2024)}
    serie.update({("nuevo", a): {} for a in (2024, 2025)})
    serie.update({("huerfano", a): {} for a in (2024, 2025)})
    ctrl = {c["codigo"]: c["marcas"] for c in aduana.control_codigos(
        serie, ["viejo", "nuevo", "huerfano", "vacio"], (2002, 2025), {"SA2022": 2024},
        {"viejo": "nuevo"})}
    assert ctrl["viejo"] == "muere_en_enmienda"
    assert ctrl["nuevo"] == "nace_en_enmienda"
    assert ctrl["huerfano"] == "nace_en_enmienda;sin_empalme"
    assert ctrl["vacio"] == "vacio"


def test_serie_no_imputa_secreto():
    s = aduana.serie_por_codigo([Registro(2020, "A", "X", 10.0, None, 1),
                                 Registro(2020, "A", "Y", 5.0, 2.0, 2)])
    assert s[("A", 2020)]["kg"] == 2.0 and s[("A", 2020)]["celdas_sin_kg"] == 1
    assert s[("A", 2020)]["valor_usd"] == 15.0


def test_deflactor():
    idx = {2020: {"indice": 100.0, "meses": 12}, 2025: {"indice": 125.0, "meses": 11}}
    f = aduana.deflactar([{"anio": 2020, "valor_usd": 100.0}], 2025, indice=idx)[0]
    assert f["valor_usd_2025"] == pytest.approx(125.0)
    with pytest.raises(ValueError):
        aduana.deflactar([], 2025, indice={2025: {"indice": 1.0, "meses": 6}})
