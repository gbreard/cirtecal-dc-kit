"""Inventario: validación de la planilla de data centers y métricas de cobertura.

La planilla (plantillas/inventario.csv) la carga una persona, registro por registro, desde
fuentes primarias. Este módulo NO escribe datos: revisa y avisa. Dos niveles:
  error  el registro no se puede usar así (falta un campo obligatorio, valor fuera de
         vocabulario, MW sin base declarada, fuente = directorio de descubrimiento, ...)
  aviso  se puede usar, pero hay algo que revisar (fuente que es un directorio, tipo_uso
         distinto del que da la regla, operativo sin coordenada, ...)

Criterios (los mismos de la corrida argentina):
- Fuente primaria: la del operador, un organismo oficial o un documento verificable. Un
  directorio o agregador va en `descubierto_por`, nunca como `fuente`.
- Potencia: nunca se infiere de inversión, m² o kVA. Si hay `capacidad_mw`, `base_mw`
  dice si es IT, bruta o no_aclara.
- Conteo base: queda FUERA todo registro con flag no_verificado o posible_duplicado:<dc>.
- tipo_uso: se carga; la regla de abajo lo sugiere y avisa si no coincide.

Salidas: inventario_validacion.csv (una fila por problema), inventario_metricas.csv.
Uso:  python -m kit.inventario  (sale con código 1 si hay errores)
"""
from __future__ import annotations

import re
import sys
import unicodedata
from collections import Counter

from . import comun

OBLIGATORIOS = ("nombre", "estado", "tipo_uso", "confianza", "fuente", "fecha_relevamiento")
VOCAB = {
    "estado": {"operativo", "construccion", "anunciado", "planificado", "desconocido"},
    "tipo_uso": {"interconexion", "transaccional", "publico", "corporativo_academico",
                 "computo_intensivo", "ia_escala_anunciado"},
    "base_mw": {"IT", "bruta", "no_aclara"},
    "mayor_1mw": {"si", "no", "desconocido"},
    "confianza": {"alta", "media", "baja", "estimada"},
    "tipo": {"hyperscale", "colo", "edge", "enterprise", "public", "mineria", "hpc"},
}
FUERA_DE_BASE = ("no_verificado", "posible_duplicado")
MW_MAX = 5000.0       # más que esto en un solo sitio es un error de carga, no un dato


def normalizar(s: str | None) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def en_conteo_base(flags: str | None) -> bool:
    return not any(t.strip().startswith(FUERA_DE_BASE)
                   for t in (flags or "").split(";") if t.strip())


def tipo_uso_regla(r: dict, reglas: dict) -> str:
    """Regla en orden: IA a escala anunciada (hiperescala no operativa) > cómputo intensivo
    (minería, supercómputo) > público > transaccional > interconexión (colocation o
    carrier) > corporativo/académico."""
    tipo, op = r.get("tipo") or "", normalizar(r.get("operador"))
    if tipo == "hyperscale" and r.get("estado") != "operativo":
        return "ia_escala_anunciado"
    if tipo in ("mineria", "cripto", "hpc"):
        return "computo_intensivo"
    if tipo == "public" or r.get("operador_tipo") == "publico" or any(
            normalizar(p) in op for p in reglas.get("operadores_publicos", [])):
        return "publico"
    if any(normalizar(p) in op for p in reglas.get("patrones_transaccional", [])):
        return "transaccional"
    if tipo == "colo" or r.get("operador_tipo") == "telco":
        return "interconexion"
    return "corporativo_academico"


def validar(filas: list[dict], reglas: dict) -> list[dict]:
    """Lista de problemas: {fila, nombre, nivel, campo, motivo}."""
    probs = []

    def p(i, r, nivel, campo, motivo):
        probs.append({"fila": i, "nombre": r.get("nombre"), "nivel": nivel,
                      "campo": campo, "motivo": motivo})

    directorios = [normalizar(d) for d in reglas.get("fuentes_directorio", [])]
    bbox = reglas.get("bbox")
    vistos: Counter = Counter(normalizar(r.get("nombre")) for r in filas)
    for i, r in enumerate(filas, start=2):          # fila 1 = encabezado
        for c in OBLIGATORIOS:
            if not (r.get(c) or "").strip():
                p(i, r, "error", c, "campo obligatorio vacío")
        for c, voc in VOCAB.items():
            v = (r.get(c) or "").strip()
            if v and v not in voc:
                p(i, r, "error", c, f"'{v}' fuera de vocabulario {sorted(voc)}")
        if vistos[normalizar(r.get("nombre"))] > 1:
            p(i, r, "error", "nombre", "nombre repetido (¿duplicado?)")
        # potencia
        mw = comun.num(r.get("capacidad_mw"))
        if (r.get("capacidad_mw") or "").strip() and mw is None:
            p(i, r, "error", "capacidad_mw", "no es un número")
        if mw is not None:
            if not 0 < mw <= MW_MAX:
                p(i, r, "error", "capacidad_mw", f"{mw} fuera de rango (0, {MW_MAX}]")
            if not (r.get("base_mw") or "").strip():
                p(i, r, "error", "base_mw", "hay MW pero no se declara si es IT, bruta o no_aclara")
            if mw > 1 and r.get("mayor_1mw") == "no":
                p(i, r, "error", "mayor_1mw", "MW > 1 marcado como 'no'")
        # coordenadas
        lat, lon = comun.num(r.get("lat")), comun.num(r.get("lon"))
        if (lat is None) != (lon is None):
            p(i, r, "error", "lat/lon", "falta una de las dos coordenadas")
        elif lat is not None and bbox and not (bbox["lat"][0] <= lat <= bbox["lat"][1]
                                               and bbox["lon"][0] <= lon <= bbox["lon"][1]):
            p(i, r, "error", "lat/lon", "coordenada fuera del país")
        elif lat is None and r.get("estado") == "operativo":
            p(i, r, "aviso", "lat/lon", "operativo sin coordenada: queda 'sin_dato' en localización")
        # fuente primaria vs descubrimiento
        f, desc = normalizar(r.get("fuente")), normalizar(r.get("descubierto_por"))
        if f and desc and f == desc:
            p(i, r, "error", "fuente", "la fuente del dato es el mismo directorio que lo descubrió")
        elif f and any(d and d in f for d in directorios):
            p(i, r, "aviso", "fuente", "la fuente es un directorio: buscar fuente primaria")
            if r.get("confianza") in ("alta", "media"):
                p(i, r, "error", "confianza", "fuente de directorio con confianza alta/media")
        # conteo base
        base = en_conteo_base(r.get("flags"))
        cb = (r.get("en_conteo_base") or "").strip().lower()
        if cb and (cb in ("si", "sí", "1", "true")) != base:
            p(i, r, "error", "en_conteo_base",
              f"no coincide con flags '{r.get('flags')}' (debería ser {'sí' if base else 'no'})")
        # tipo de uso
        sug = tipo_uso_regla(r, reglas)
        if r.get("tipo_uso") and r["tipo_uso"] != sug:
            p(i, r, "aviso", "tipo_uso", f"la regla sugiere '{sug}'")
    return probs


def metricas(filas: list[dict], ref: dict | None) -> dict:
    """Conteos y cobertura contra el agregado nacional de referencia. Entran en la
    comparación: operativos del conteo base, > 1 MW, base IT o no_aclara, y tipo_uso
    distinto de computo_intensivo e ia_escala_anunciado."""
    ops = [r for r in filas if r.get("estado") == "operativo"]
    comp = [r for r in ops if en_conteo_base(r.get("flags")) and r.get("mayor_1mw") == "si"
            and r.get("base_mw") in ("IT", "no_aclara")
            and r.get("tipo_uso") not in ("computo_intensivo", "ia_escala_anunciado")]
    mw_it = sum(comun.num(r.get("capacidad_mw")) or 0 for r in comp if r["base_mw"] == "IT")
    mw_na = sum(comun.num(r.get("capacidad_mw")) or 0 for r in comp if r["base_mw"] == "no_aclara")
    m = {"registros": len(filas), "operativos": len(ops),
         "conteo_base": sum(en_conteo_base(r.get("flags")) for r in filas),
         "operativos_conteo_base": sum(en_conteo_base(r.get("flags")) for r in ops),
         "comparables_referencia": len(comp), "mw_it": round(mw_it, 1),
         "mw_no_aclara": round(mw_na, 1)}
    if ref:
        m["cobertura_n"] = round(len(comp) / ref["operativos_mayor_1mw"], 3)
        m["cobertura_mw_it"] = round(mw_it / ref["mw"], 3)
        m["cobertura_mw_it_mas_no_aclara_cota"] = round((mw_it + mw_na) / ref["mw"], 3)
    for k, n in sorted(Counter(r.get("tipo_uso") for r in filas).items()):
        m[f"tipo_uso:{k}"] = n
    return m


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description="Validación de la planilla de inventario")
    ap.add_argument("--pais", default="config/pais.yaml")
    ap.add_argument("--planilla", help="por defecto, la de pais.yaml: inventario")
    a = ap.parse_args()
    cfg = comun.pais(a.pais)
    filas = comun.leer_csv(a.planilla or cfg["inventario"])
    probs = validar(filas, cfg.get("inventario_reglas", {}))
    m = metricas(filas, cfg.get("parque_referencia"))
    print(comun.escribir_csv(comun.salida("inventario_validacion.csv", cfg), probs))
    print(comun.escribir_csv(comun.salida("inventario_metricas.csv", cfg),
                             [{"metrica": k, "valor": v} for k, v in m.items()]))
    n_err = sum(x["nivel"] == "error" for x in probs)
    print(f"errores: {n_err} · avisos: {len(probs) - n_err}")
    sys.exit(1 if n_err else 0)


if __name__ == "__main__":
    main()
