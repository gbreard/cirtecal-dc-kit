"""inventario.py: validación de la planilla y regla de tipo_uso."""
from kit import inventario

BASE = {"nombre": "DC A", "estado": "operativo", "tipo_uso": "interconexion",
        "confianza": "alta", "fuente": "Sitio del operador", "fecha_relevamiento": "2026-10-14",
        "tipo": "colo"}
REGLAS = {"fuentes_directorio": ["Directorio X"], "operadores_publicos": ["Estatal"],
          "patrones_transaccional": ["banco"]}


def _errores(filas):
    return {(p["campo"], p["nivel"]) for p in inventario.validar(filas, REGLAS)}


def test_planilla_valida_sin_errores():
    assert not [p for p in inventario.validar([dict(BASE)], REGLAS) if p["nivel"] == "error"]


def test_mw_sin_base_es_error():
    assert ("base_mw", "error") in _errores([{**BASE, "capacidad_mw": "5"}])


def test_directorio_no_es_fuente():
    e = _errores([{**BASE, "fuente": "Directorio X", "descubierto_por": "Directorio X"}])
    assert ("fuente", "error") in e
    e = _errores([{**BASE, "fuente": "Directorio X (ficha)"}])
    assert ("fuente", "aviso") in e and ("confianza", "error") in e


def test_conteo_base_y_vocabulario():
    e = _errores([{**BASE, "flags": "no_verificado", "en_conteo_base": "sí"},
                  {**BASE, "nombre": "DC B", "estado": "abierto"}])
    assert ("en_conteo_base", "error") in e and ("estado", "error") in e
    assert inventario.en_conteo_base("ubicacion_no_confirmada")
    assert not inventario.en_conteo_base("posible_duplicado:DC A")


def test_regla_tipo_uso():
    r = inventario.tipo_uso_regla
    assert r({"tipo": "hyperscale", "estado": "anunciado"}, REGLAS) == "ia_escala_anunciado"
    assert r({"tipo": "mineria", "estado": "operativo"}, REGLAS) == "computo_intensivo"
    assert r({"operador": "Banco Sur", "tipo": "enterprise"}, REGLAS) == "transaccional"
    assert r({"operador": "Estatal SA", "tipo": "colo"}, REGLAS) == "publico"
    assert r({"tipo": "enterprise"}, REGLAS) == "corporativo_academico"


def test_metricas_excluyen_computo_intensivo():
    filas = [{**BASE, "mayor_1mw": "si", "base_mw": "IT", "capacidad_mw": "4"},
             {**BASE, "nombre": "Mina", "tipo_uso": "computo_intensivo", "mayor_1mw": "si",
              "base_mw": "IT", "capacidad_mw": "12"}]
    m = inventario.metricas(filas, {"operativos_mayor_1mw": 4, "mw": 40.0})
    assert m["comparables_referencia"] == 1 and m["cobertura_mw_it"] == 0.1
