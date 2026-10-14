# De dcarg al kit CIRTECAL: mapa de origen

El kit se armó **copiando y generalizando** el paquete `dcarg` (proyecto dc-argentina-ia,
oct-2026). No se modificó nada de `dcarg`, `data/` ni de las versiones congeladas. El kit
no importa `dcarg`: corre solo (verificado copiándolo fuera del repositorio, 41 tests OK).

## 1. Qué archivo de dcarg dio origen a cada archivo del kit

| Archivo del kit | Origen en dcarg | Qué cambió al generalizar |
|---|---|---|
| `config/pais.yaml` | `config.py` (umbrales de conectividad, `CONECT_IXP_PRINCIPAL`), `referencia.py` (`CABASE_*`), `conectividad/aterrizajes.py` (estaciones), `metricas.py` (AMBA) | Todo lo argentino pasó a un archivo de datos: nodo principal y estaciones con coordenada y fuente, parque de referencia, región principal, reglas del inventario y enmiendas vigentes. |
| `config/parametros.yaml` | `raee.py` (`VIDA_UTIL`), `mwbom/parametros.py` (`U`, `PARAMS`, `FUENTES`), `config.py` (`ESPEJO_*`), `comercio/espejo.py` (`HUBS`), `specs/hallazgos/C4` (cortes estricto/laxo) | Cada valor con fuente y estado (verificado / parcial / supuesto) al lado. La vida útil sigue siendo un solo parámetro, compartido por raee y mwbom. |
| `config/canasta_sa6.csv` | `raee.py` (`CANASTA_RAEE`), `comercio/capas.py` (`CAPA_POR_HS6`), `mwbom/parametros.py` (`FAMILIAS_NCM`, `TIPO_VIDA`), `comercio/canasta.py` (tags) | Canasta común a 6 dígitos con capa, canasta (`aee_estricta`, `inversion`, `sensibilidad`, `indicativa`), serie RAEE, tipo de vida, familia de mwbom y correspondencias del SA2022 (ver §3, punto 5). |
| `config/canasta_ar_ncm8.csv` | `comercio/canasta.py` (`CANASTA`, `EMPALME_C5`, `SENSIBILIDAD`) y la tabla `ncm_canasta` de la DB | Extensión argentina a 8 dígitos, exportada de la DB (lo que realmente corrió), con `sucesor_empalme` y `sensibilidad`. |
| `config/deflactor_cpiu_anual.csv` | `data/raw/deflactores/CUSR0000SA0_anual.csv` (de `deflactor.py`) | Copia (BLS, dominio público). |
| `kit/comun.py` | `config.py` (rutas), `dedupe._haversine_m` | Nuevo: lectura de YAML y CSV, rutas relativas a la raíz del kit, haversine. |
| `kit/inventario.py` | `validador.py`, `decisiones.py` (`en_conteo_base`, `FUERA_DE_BASE`), `uso.py` (`tipo_uso`), `metricas.py` (cobertura CABASE) | Valida una planilla en vez de escribir en SQLite. Agrega dos controles: fuente = directorio de descubrimiento (error) y MW sin base (error). La regla de tipo_uso sugiere y avisa; no pisa lo cargado. |
| `kit/localizacion.py` | `conectividad/cruce.py` (`cruce_dc`, `logica`), `metricas.py` (`_amba`) | La motivación energética pasó de un diccionario en config a una columna del inventario. La región principal es configurable. |
| `kit/aduana.py` | `comercio/series.py`, `comercio/canasta.py` (empalme), `comercio/capas.py`, `deflactor.py` | Nuevo control de códigos vacíos y de versionado: nace o muere en un año de enmienda, sin empalme declarado. En dcarg era un hallazgo manual (C-5); acá es automático. |
| `kit/espejo.py` | `comercio/espejo.py` (`clasificar`, `cruzar`, `reclasificar`) | Sin DB ni red: recibe dos tablas (espejo y aduana a SA6 completo). Los cortes de sensibilidad (estricto / base / laxo) se corren siempre. |
| `kit/mwbom.py` | `mwbom/modelo.py` (`bom_fisico`, `reconciliar`, `correr_caso`, `atribucion`), `mwbom/parametros.py` (`casos`) | Los casos salen de pais.yaml y del inventario. Stargate dejó de ser un caso fijo: cualquier `ia_escala_anunciado` con MW es un anuncio. f se guarda sin redondear. |
| `kit/raee.py` | `raee.py`, `raee_revision.py` (segunda vida, triangular) | Agrega la variante B (segunda vida) con balance hasta el descarte y el nivel data center con f fijo. |
| `kit/fuentes/aduana_plantilla.py` | `collectors/base.py`, `comercio/registro.py` | Interfaz mínima: año, código, origen, valor, kg. Incluye `ArchivoCSV` para países sin API. |
| `kit/fuentes/aduana_ar.py` | `collectors/indec_comex.py`, `comercio/espejo.py` (`indec_hs6_por_pais`, `subposiciones_hs6`) | Implementación de ejemplo de la interfaz. |
| `kit/fuentes/comtrade.py` | `collectors/comtrade.py` | La clave va por variable de entorno (`COMTRADE_API_KEY`), con endpoint público si no hay clave. Sin `curl --resolve` con IP fija ni escritura en DB. Socio = M49 de pais.yaml. |
| `kit/fuentes/peeringdb.py` | `conectividad/peeringdb.py`, `conectividad/capas.py` (`capa_ixp`) | País por ISO2 de pais.yaml. Pausa mínima de 2 s forzada en el código. Crudo solo en la caché local. |
| `kit/fuentes/http.py` | `collectors/base.py` (`http_get`), `peeringdb._solo_ipv4` | User-Agent sin correo, pausa por host y caché fuera del repositorio. Un 403 o 429 corta (`Bloqueado`). |
| `plantillas/inventario.csv`, `inventario_campos.csv` | Columnas de `cierre.COLS_V13` y criterios de `CONSTITUTION.md` (P1, P6), `decisiones.py`, `tengodata.py` | Agrega `operador_tipo`, `fuente_url` y `motivacion_energetica_fuente`. |
| `ejemplo_ar/inventario_v1_3.csv` | `data/processed/inventario_v1_3.csv` | Copia. |
| `ejemplo_ar/importaciones_anual.csv` | Tabla `comercio_importaciones` de la DB | Agregado por año y código: sin origen y sin mes. |
| `ejemplo_ar/espejo_brecha_por_causa.csv` | `data/processed/c4_espejo_subregistro.csv` | Agregado por SA6, año y causa: sin valores por país informante. |
| `ejemplo_ar/m49_origen.csv` | `comercio/espejo.py` (`M49_INDEC`) | Copia como datos. |
| `ejemplo_ar/publicado_*.csv` | `data/processed/atribucion_dc.csv`, `raee_estimado_banda.csv`, `deck/raee_comprometido_2027_2030.csv` | Copias, como referencia de los tests. |
| `ejemplo_ar/resultados/` | — | Salidas del kit sobre el ejemplo. |
| `tests/test_kit_raee.py` | `tests/test_raee.py`, `tests/test_raee_revision.py` | Sin DB: datos sintéticos. |
| `tests/test_kit_mwbom.py` | `tests/test_mwbom.py` | Sin DB. |
| `tests/test_kit_espejo.py` | `tests/test_comercio_espejo.py` | Sin red ni DB. |
| `tests/test_kit_aduana.py` | `tests/test_comercio_series.py`, `tests/test_deflactor.py` | Nuevo test del control de códigos. |
| `tests/test_kit_inventario.py` | `tests/test_validador.py`, `tests/test_decisiones.py`, `tests/test_uso.py` | |
| `tests/test_kit_localizacion.py` | `tests/test_conectividad.py` | |
| `tests/test_kit_fuentes.py` | — | Nuevo: interfaz, pausa mínima de PeeringDB, User-Agent sin correo, 403 no forzado. |
| `tests/test_kit_ejemplo_ar.py` | — | Nuevo: reproduce f 0,163, RAEE DC 2026 = 503 t, 2027–2030 = 1.501 t, la banda completa, las métricas del inventario y las distancias. |

**No pasaron al kit** porque no forman parte de los seis métodos o son propios del
relevamiento argentino:
- `rigi.py`
- `tengodata.py`
- `novedades.py`
- `candidatos.py`
- `uptime.py`
- `capacidad.py`
- `cripto.py`
- `deck.py`
- `versiones.py`
- `uso.py`, la parte de CDN y programas de caché
- `viz/`
- `llm/`
- `geo/`
- `collectors/datacentermap.py`, `prensa.py` y `seed.py`
- la base SQLite

## 2. Verificación

- **41 tests pasan,** dentro del repositorio y en una copia aislada fuera de él.
- **Las cifras publicadas se reproducen:**
  - f = 0,1626 (0,163).
  - RAEE DC 2026 = 503.461 kg, el mismo kilo que `atribucion_dc.csv`.
  - La banda de RAEE completa (las tres series, todos los años) coincide a menos de 1 kg.
  - El inventario da 41 / 33 / 39 registros y cobertura 3 de 13 (7,6 MW IT, 23,7 %).
  - La lógica de localización coincide en los 41 registros, y las distancias al nodo
    principal difieren en menos de 0,15 km.
- **Cada módulo corre con un solo comando** (`python -m kit.<modulo>`). `kit.espejo`
  necesita antes `kit.fuentes.comtrade` y, si falta el insumo, lo dice sin traza de error.

**¿503 o 504 t en 2026? Es 503 t.** La diferencia es solo el redondeo de f:

| f usado | 2026 | 2027–2030 |
|---|---|---|
| Sin redondear (0,162556) | **503 t** | **1.500 t** |
| Redondeado a 4 decimales (0,1626) | 504 t | 1.501 t |

- La cifra publicada de 2026 usó f sin redondear.
- La de 2027–2030 (1.501 t) usó f redondeado.
- Las 504 t de la revisión del RAEE del 14-oct también usaban f redondeado.
- Para que sean coherentes, conviene citar 503 t y 1.500 t (diferencia < 0,1 %).
- El test reproduce las dos convenciones y las deja explícitas.

## 3. Qué quedó sin generalizar, y por qué

1. **El lado aduana del espejo a SA6 completo.** Depende de cómo cada aduana permite pedir
   un SA6 entero. En INDEC hay que listar las subposiciones, y para eso hace falta el
   nomenclador de la NCM, que no se incluye: es un archivo de AFIP que se baja aparte.
   - El kit define el método (`importaciones_sa6`) y acepta una planilla exportada.
   - No hay una implementación genérica posible.
2. **El ejemplo argentino del espejo no se puede re-correr.** El crudo de Comtrade no se
   redistribuye. El ejemplo trae solo la descomposición agregada por causa, y el test del
   espejo usa datos sintéticos.
3. **El mapeo entre informantes de Comtrade y orígenes de la aduana** (`m49_origen.csv`) es
   por país, porque cada aduana nombra los orígenes a su manera. Comtrade usa códigos casi
   M49, con excepciones: Francia 251, Suiza 757, Estados Unidos 842. Cada equipo arma el
   suyo.
4. **Las correspondencias de enmiendas a 8 dígitos son nacionales.** El kit las toma de la
   canasta nacional (`sucesor_empalme`), pero el trabajo de encontrarlas es de cada equipo,
   contra la glosa oficial de su nomenclatura.
5. **Correspondencias del SA2022 a 6 dígitos.**
   - **Incluidas:** solo dos.
     - 8517.70 → 8517.71 / 8517.79: verificado en la serie argentina.
     - Parte de 8473.30 → 8524 (módulos de pantalla): **marcado "a verificar"** contra la
       tabla de correlación de la OMA, que no se consultó en esta tarea.
   - **Pendiente:** completar la tabla con la correlación oficial antes de difundirla como
     "canasta común".
6. **Nacimientos del SA2007 sin empalme** (8471.49, 8471.80, 8517.62.x y otros). En la
   corrida argentina se documentaron como subestimación previa a 2007, sin empalmar. El kit
   los marca (`sin_empalme`) pero no los resuelve.
7. **El caso Stargate.** La auditoría de anuncios se generalizó (todo `ia_escala_anunciado`
   con MW, perfil IA, ventana `ventana_anuncios` de pais.yaml). Lo que no se trasladó es la
   lectura: en IA hay que comparar en US$, no en kg. El kit da las dos columnas, pero la
   interpretación ("lo importado equipa a lo sumo X MW") queda en el informe de cada país.
8. **La regla de `tipo_uso` depende de `operador_tipo`,** que el inventario v1.3 no tiene
   (en dcarg vivía en la tabla de operadores). Por eso el ejemplo da 4 avisos explicables.
9. **Lo que no entra en los seis métodos y quedó afuera:** el uso del parque por PeeringDB
   (`uso.py`), es decir, la detección de CDN extranjeras y de programas de caché. El módulo
   `peeringdb.py` sí trae `redes_por_facility`, pero la clasificación de redes es una lista
   de ASN revisada a mano para Argentina y no se trasladó.
10. **Geocodificación.** El kit no geocodifica: las coordenadas vienen en la planilla. En
    dcarg, `geo/` usaba Nominatim con caché. Un geocodificador automático tienta a ubicar
    macrorregiones (contra la regla P6), así que la decisión queda en la persona que carga.
11. **El chequeo de magnitud del RAEE** usa el Global E-waste Monitor y la población del
    país, que cada equipo tiene que cargar en pais.yaml. Si faltan, el chequeo se omite sin
    error.
12. **El deflactor** usa el CPI-U de EE.UU. para todos los países, porque las series están
    en US$. La versión hedónica (índice de precios de importación de computadoras), que en
    dcarg era sensibilidad, no se trasladó.
