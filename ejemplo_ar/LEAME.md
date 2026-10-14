# Ejemplo: corrida argentina (oct-2026)

Insumos y resultados de la corrida argentina, para comprobar que el kit funciona y para
ver qué forma tienen los resultados. **Hay solo agregados y el inventario v1.3.** No hay
nada crudo de PeeringDB, de Comtrade ni de INDEC.

`tests/test_kit_ejemplo_ar.py` corre el kit sobre estos insumos y reproduce las cifras
publicadas.

## Archivos

| Archivo | Qué es | Origen y condiciones |
|---|---|---|
| `inventario_v1_3.csv` | Inventario de data centers, 41 registros (10-oct-2026) | Elaboración propia (CC BY 4.0). Trece registros llevan Tengo Data (CC BY 4.0, versión 23/09/2026) en `descubierto_por`; el dato sale de la fuente primaria citada en cada uno. No tiene la columna `operador_tipo` de la plantilla (ver avisos abajo). |
| `importaciones_anual.csv` | Importación por año y código NCM de la canasta (2002–2026-08): US$ CIF, kg y meses con dato. Sin origen y sin mes. | Agregado propio de la serie de INDEC (comercio exterior, public-api). Dato público, se cita "Fuente: INDEC". |
| `espejo_brecha_por_causa.csv` | Brecha espejo por SA6, año y causa (2023–2025): celdas y US$ | Agregado propio del cruce INDEC × UN Comtrade. **No incluye los valores por país informante**: el crudo de Comtrade no se redistribuye. |
| `m49_origen.csv` | Código M49 del informante → nombre del origen en INDEC | Elaboración propia |
| `publicado_atribucion_dc.csv`, `publicado_raee_estimado_banda.csv`, `publicado_raee_comprometido_2027_2030.csv` | Cifras publicadas, tal como salieron del sistema original (dcarg) | Elaboración propia. Son la referencia de los tests. |
| `resultados/` | Salidas del kit sobre estos insumos | Elaboración propia (CC BY 4.0) |

En `config/` hay además insumos argentinos o de terceros:
- `pais.yaml`: tiene coordenadas de OpenStreetMap (ODbL) y de PeeringDB.
- `canasta_ar_ncm8.csv`: elaboración propia.
- `deflactor_cpiu_anual.csv`: datos del BLS, de dominio público.

## Cifras que el ejemplo reproduce

| Cifra | Publicada | Kit | Nota |
|---|---|---|---|
| Factor de atribución f (central) | 0,163 | 0,16256 | banda 0,109–0,233 |
| RAEE DC 2026 (central) | 503 t | 503,5 t | banda 321–573 t |
| RAEE DC 2027–2030 (central, acumulado) | 1.501 t | 1.500,1 t (f sin redondear) / 1.501 t (f = 0,1626) | ver abajo |
| RAEE IT nacional 2026 (central) | 3.097 t | 3.097 t | banda 2.465–3.097 t |
| Inventario: registros / operativos / conteo base | 41 / 33 / 39 | igual | |
| Cobertura del agregado CABASE | 3 de 13; 7,6 MW IT (23,7 %) | igual | |

**¿2026 es 503 o 504 t?** Es **503 t**. Las dos parejas salen del mismo modelo; lo único
que cambia es el redondeo de f:

| f usado | 2026 | 2027–2030 |
|---|---|---|
| Sin redondear (0,162556) | **503 t** | **1.500 t** |
| Redondeado a 4 decimales (0,1626) | 504 t | 1.501 t |

- La cifra publicada de 2026 se calculó con f sin redondear.
- La de 2027–2030 se calculó con f redondeado (`deck/raee_comprometido_2027_2030.csv`).
- Las 504 t que aparecieron en la revisión del RAEE (14-oct-2026) usaban también f
  redondeado.
- **Para que sean coherentes, conviene citar 503 t y 1.500 t.** La diferencia es menor al
  0,1 % y no cambia ninguna conclusión.

## Lo que el control de códigos encuentra en Argentina (`resultados/aduana_control_codigos.csv`)

29 de los 79 códigos de la canasta tienen alguna marca:

- **Nacimientos en 2007 sin predecesor declarado** (`nace_en_enmienda;sin_empalme`): 8471.49,
  8471.80, 8517.62.x, 8517.70.x, 8544.42 y 8418.69.40. Son las posiciones nuevas del SA2007.
  En la serie argentina se documentaron como subestimación previa a 2007, sin empalme.
- **La enmienda 2022 (vigente desde 2024-01) con empalme declarado:** 8471.41, 8471.70.1x,
  8473.30.99 → .90, 8517.62.31/.32/.48 y 8517.70.x → 8517.79.
- **Dos hallazgos que el control deja a la vista:**
  - 8471.70.40 (SSD) nace en 2024 sin predecesor en la canasta. Habría que buscarlo antes
    de leer un crecimiento del almacenamiento.
  - 9403.20.90 (racks) nace en 2024 y su predecesor, 9403.20.00, no está declarado como
    empalme. En la corrida original se documentó a mano.
- **Vacíos:** 8528, 8541, 8542.31 y 8542.32. Son códigos de 4 o 6 dígitos que la API de
  INDEC no responde. Son de sensibilidad y nunca se cargaron.

## Avisos de la validación del inventario (0 errores, 22 avisos)

- 17 operativos sin coordenada: quedan `sin_dato` en localización. Es lo esperado: no se
  geocodifica sin dirección.
- 1 registro con fuente de directorio, con confianza baja.
- 4 avisos de `tipo_uso`, todos explicables:
  - **Telecom Pacheco, Movistar Pacheco y Claro San Telmo:** el inventario v1.3 no tiene la
    columna `operador_tipo`. En dcarg, el tipo "telco" del operador los llevaba a
    `interconexion`. Con la planilla nueva, completar `operador_tipo = telco` los alinea.
  - **BCRA:** el patrón "banco" sugiere `transaccional`, pero el operador es estatal y en
    v1.3 quedó `publico`. Gana el valor cargado. La regla solo avisa.
