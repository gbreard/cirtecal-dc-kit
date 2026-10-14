# Kit de réplica CIRTECAL

Seis métodos para medir, desde fuentes públicas, la infraestructura de centros de datos de
un país y el residuo electrónico que deja. Salió de la investigación argentina
(oct-2026) y está generalizado para que cualquier equipo del consorcio lo corra con sus
datos.

**Punto de entrada a los métodos:** [docs/README.md](docs/README.md). Cada método tiene
su ficha: qué pregunta responde, con qué fuentes y qué trampas encontramos. Este README
explica cómo correr el código.

**Requisitos:** Python 3.10 o más nuevo, y `pip install -r requirements.txt`.
No usa ninguna herramienta de inteligencia artificial ni servicios pagos. Comtrade y
PeeringDB funcionan sin clave, con límites más bajos.

## Qué mide

| # | Módulo | Pregunta | Insumo mínimo |
|---|---|---|---|
| 1 | `kit.inventario` | ¿Qué data centers hay, en qué estado y con qué potencia? ¿Cuánto del agregado nacional cubre el relevamiento? | la planilla `plantillas/inventario.csv` completada |
| 2 | `kit.localizacion` | ¿Los data centers se ubican por conectividad o por energía? | inventario con coordenadas, nodo principal de intercambio y estaciones de amarre |
| 3 | `kit.aduana` | ¿Cuánto equipamiento de data center se importa, en valor y en peso? ¿Hay quiebres por cambio de nomenclatura? | importaciones por código, año y origen |
| 4 | `kit.espejo` | ¿Cuánto de lo que los socios dicen exportar no aparece en la aduana, y por qué? | aduana a 6 dígitos por origen y exportaciones de los socios (Comtrade) |
| 5 | `kit.mwbom` | ¿Cuánto equipo implica la potencia instalada y qué fracción de la importación IT es de data centers (factor de atribución f)? | potencia de referencia (MW) y la serie de aduana |
| 6 | `kit.raee` | ¿Cuántas toneladas de residuo IT salen de uso por año, y cuánto es de data centers? | serie de aduana en kg y f |

Todos los resultados se dan en banda (tres escenarios), nunca como un número único.
Ningún módulo inventa un dato: si falta, la celda queda vacía y se informa.

## Orden de corrida

```bash
cd cirtecal-dc-kit
python -m pytest -q tests                       # 0. el kit funciona (corre el ejemplo argentino)

python -m kit.inventario                        # 1. valida la planilla (sale con error si hay)
python -m kit.fuentes.peeringdb                 # 2a. (opcional) sedes de IXP del país
python -m kit.localizacion                      # 2b. distancias y lógica
python -m kit.aduana                            # 3. serie, empalme, control de códigos
python -m kit.fuentes.comtrade --sa6 8471.50 8473.30 --anios 2023 2025   # 4a. espejo
python -m kit.espejo --bajar-aduana             # 4b. cruce (o con espejo_aduana.csv propio)
python -m kit.mwbom                             # 5. MW -> equipo -> aduana y f
python -m kit.raee                              # 6. RAEE (banda, segunda vida, nivel DC)
```

Los resultados quedan en `salidas/`, que no se versiona. Cada módulo es un solo comando.
`aduana`, `mwbom` y `raee` recalculan lo que necesitan de los anteriores, así que se pueden
correr sueltos.

## Qué adapta cada país

**Obligatorio: `config/pais.yaml`.** Hay que completar:
- país y código M49;
- la fuente aduanera: el módulo o la planilla exportada;
- los años y el último período con dato;
- el nodo principal de intercambio (coordenada y fuente);
- las estaciones de amarre (coordenadas y fuente).

Con eso corren los seis métodos.

**Según el país:**

| Archivo | Qué hacer |
|---|---|
| `kit/fuentes/aduana_<pais>.py` | Implementar la interfaz de `aduana_plantilla.py`, que devuelve año, código, origen, valor y kg. `aduana_ar.py` (INDEC) es el ejemplo. **Si la aduana no tiene API, no hace falta programar:** se exporta una planilla con esas cinco columnas y se pone su ruta en `fuente_aduanera.archivo`. |
| `config/canasta_<pais>.csv` | Abrir la canasta común de 6 dígitos (`canasta_sa6.csv`) en la nomenclatura nacional. Declarar en `sucesor_empalme` los códigos viejos que la enmienda 2022 fusionó en uno nuevo. `canasta_ar_ncm8.csv` es el ejemplo. Sin este archivo, el kit trabaja a 6 dígitos. |
| `pais.yaml`, `enmiendas_vigencia` | Año en que cada enmienda del SA entró en vigor en la nomenclatura nacional. Puede llegar con rezago: en Argentina, el SA2022 rige desde 2024. |
| `pais.yaml`, `parque_referencia` | Agregado nacional publicado (cantidad de data centers de más de 1 MW, MW, base IT o bruta). Es opcional, pero sin él no hay factor de atribución contra un parque nacional. |
| `pais.yaml`, `inventario_reglas` | Operadores estatales, patrones de operadores transaccionales, directorios que no cuentan como fuente y recuadro de coordenadas del país. |
| `ejemplo_<pais>/m49_origen.csv` | Correspondencia entre el código del informante en Comtrade y el nombre del origen en la aduana propia. |
| `config/parametros.yaml` | Por lo general no se toca. Cada valor lleva su fuente y su estado (verificado, parcial o supuesto). Si un equipo tiene un dato mejor y verificado, cambiarlo es legítimo, y conviene avisar al consorcio. |

## Reglas que el kit hace cumplir (y que conviene no saltear)

1. **Fuente primaria.** Un directorio o agregador sirve para *descubrir* un sitio y se
   anota en `descubierto_por`. El dato sale de la fuente del operador o de un organismo
   oficial.
2. **No se infiere potencia** a partir de inversión, m², kVA o cantidad de racks. Si hay
   MW, se declara su base (IT, bruta o no_aclara).
3. **No se geocodifica una macrorregión.** Sin dirección, no hay coordenada, y la
   localización queda `sin_dato`.
4. **Versionado de nomenclatura.** Un código que "nace" en un año de enmienda no es un
   crecimiento real hasta que se empalma con su predecesor. `aduana_control_codigos.csv`
   lista los códigos sospechosos.
5. **Secreto estadístico.** Las celdas sin valor o sin peso no se imputan.
6. **Espejo a 6 dígitos contra 6 dígitos.** Comparar contra la canasta (un subconjunto)
   infla la brecha.
7. **Misma vida útil en W y en f.** El factor de atribución y el RAEE se corren siempre con
   el mismo escenario.
8. **Consultas responsables.**
   - User-Agent del proyecto, sin correo personal.
   - Pausas mínimas: 2 s para INDEC, 2–6 s para PeeringDB y 1,5 s para Comtrade.
   - Un 403 o un 429 corta la consulta, no se insiste.
   - Los crudos quedan en `~/.cache/kit_cirtecal` (variable `KIT_CACHE`), **fuera del
     repositorio**, y no se redistribuyen.
9. **Claves solo por variable de entorno:** `COMTRADE_API_KEY` y `PEERINGDB_API_KEY`.

## Estructura

```
docs/         fichas de método (empezar por docs/README.md)
config/       pais.yaml · parametros.yaml · canasta_sa6.csv · canasta_ar_ncm8.csv · deflactor_cpiu_anual.csv
kit/          comun.py · inventario.py · localizacion.py · aduana.py · espejo.py · mwbom.py · raee.py
kit/fuentes/  aduana_plantilla.py · aduana_ar.py · comtrade.py · peeringdb.py · http.py
plantillas/   inventario.csv (planilla vacía con una fila de ejemplo) · inventario_campos.csv (criterios)
ejemplo_ar/   insumos agregados y resultados de la corrida argentina (ver ejemplo_ar/LEAME.md)
tests/        un archivo por módulo + test_kit_ejemplo_ar.py (reproduce las cifras publicadas)
```

## Cómo leer los resultados

- **Banda:** corto, central y largo son escenarios de vida útil.
  - Corto: reposición rápida, de hiperescala.
  - Central: ciclo de servidor empresarial.
  - Largo: con reúso.
- **Las cifras se citan como central con su banda.**
- **`horizonte = comprometido`:** residuo de equipos que ya entraron al país y todavía no
  salieron de uso. Es un piso, porque no incluye importaciones futuras.
- **Baterías:** van en una serie aparte, de doble uso (automotor, solar). Nunca se suman
  al residuo IT.
- **Factor f:** es un cociente entre flujos, no una medición. Se reporta con su banda y con
  la sensibilidad a la base de los MW (IT o bruta).

## Licencia y cita

El código va con licencia MIT, y la documentación y los datos propios con CC BY 4.0 (ver
`LICENSE`). Los datos de terceros tienen sus propias condiciones, listadas en
`ejemplo_ar/LEAME.md`.

Cita sugerida: *Kit de réplica CIRTECAL — métodos para medir infraestructura de centros de
datos y RAEE desde fuentes públicas (v1.0, oct-2026).*

## Cómo aportar

Errores, clasificaciones arancelarias que el kit no mira y trampas nuevas: ver [CONTRIBUTING.md](CONTRIBUTING.md). Todo aporte trae su fuente.
