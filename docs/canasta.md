# La canasta de posiciones arancelarias

Ninguna posición arancelaria «es de IA». El equipamiento de un centro de datos se reparte entre decenas de posiciones que también registran bienes de otros usos. Por eso la canasta se arma **por componentes**, posición por posición, y cada una lleva su motivo, su canasta y sus cuidados. Esta página es la explicación de [`config/canasta_sa6.csv`](../config/canasta_sa6.csv) y la primera que conviene revisar y corregir para cada país.

## Cómo leer la canasta

| Columna del CSV | Qué indica |
|---|---|
| `sa6` | Subpartida del Sistema Armonizado a 6 dígitos: común a todos los países |
| `capa` | Cómputo, red, energía, refrigeración o infraestructura física |
| `canasta` | **aee_estricta**: se vuelve RAEE y alimenta el método 6. **inversion**: mide el gasto en la obra. **sensibilidad**: solo para pruebas. **indicativa**: señal cualitativa, fuera de las series |
| `serie_raee` | **limpia**: atribuible al cómputo. **cota_superior**: mezcla usos. **baterias**: serie aparte |
| `tipo_vida` | Qué escenario de vida útil se le aplica (cómputo, almacenamiento, red, baterías) |
| `familia_mwbom` | Con qué familia de equipos se compara en el método 5 |
| `enmienda_2022` / `nota_enmienda` | Cambios de la enmienda 2022 del SA que obligan a empalmar |

La extensión nacional (en Argentina, [`config/canasta_ar_ncm8.csv`](../config/canasta_ar_ncm8.csv)) abre cada subpartida a la nomenclatura del país y agrega columnas de juicio: solapamiento con otros usos (`doble_uso`), si es cota superior y el código sucesor para empalmar (`sucesor_empalme`).

## Las posiciones, por capa

### Cómputo (canasta AEE estricta)
| SA6 | Qué registra | Cuidado |
|---|---|---|
| 8471.41 | Máquinas de procesamiento de datos completas, en una misma envoltura | Incluye computadoras de uso general; según el país, aquí pueden ir sistemas de IA integrados |
| 8471.49 | Máquinas presentadas en forma de sistemas | Donde suelen declararse los sistemas acelerados completos (tipo HGX/DGX) |
| 8471.50 | Unidades de proceso: servidores | La posición más propia de un centro de datos |
| 8471.70 | Unidades de almacenamiento (discos, arreglos) | Revisar códigos nuevos sin predecesor (en Argentina, 8471.70.40 de SSD desde 2024) |
| 8471.80 | Las demás unidades de máquinas de procesamiento | Residual |
| 8473.30 | Partes y accesorios de 8471, **incluidos los aceleradores (GPU) sueltos** | Mezcla placas de uso doméstico, *gaming* y minería: **cota superior**. La enmienda 2022 pasó parte a 8524 (módulos de pantalla): verificar con la tabla de la OMA |
| 8523.51 | Almacenamiento no volátil (flash, SSD) | También es de consumo masivo |

### Red (canasta AEE estricta, salvo cables)
| SA6 | Qué registra | Cuidado |
|---|---|---|
| 8517.62 | Conmutadores y enrutadores | Incluye equipamiento de redes de acceso y empresas |
| 8517.70 → 8517.71 / 8517.79 | Partes de aparatos de telecomunicaciones | La enmienda 2022 la dividió: sin empalme, la serie «nace» en el año de vigencia. **Cota superior** |
| 8544.42 | Conductores con piezas de conexión | Inversión; uso muy general |
| 8544.70 | Cables de fibra óptica | Inversión; incluye redes de telecomunicaciones |

### Energía
| SA6 | Qué registra | Canasta | Cuidado |
|---|---|---|---|
| 8504.40 | Convertidores estáticos (UPS, fuentes) | inversión | Uso industrial y residencial: cota superior |
| 8504.21 / .22 / .23 / .33 | Transformadores por potencia | inversión | Cota superior |
| 8502.12 / .13 | Grupos electrógenos diésel | inversión | Cota superior |
| 8536.20 / .50 / .69 / .90 | Disyuntores, interruptores, conectores, PDU | inversión | Uso general |
| 8537.10 / .20 | Tableros | inversión | Uso general |
| 8507.20 | Acumuladores de plomo **excepto los de arranque** | AEE, serie aparte | Los de arranque de motores van en **8507.10**, fuera de la canasta |
| 8507.60 | Acumuladores de iones de litio | AEE, serie aparte | Incluye movilidad y almacenamiento solar; el más sensible a la vida útil |

### Refrigeración (inversión)
| SA6 | Qué registra | Cuidado |
|---|---|---|
| 8415.82 / .83 | Aire acondicionado de precisión (CRAC/CRAH) | También climatización comercial |
| 8418.69 | Enfriadores (*chillers*) | Uso industrial |
| 8419.50 | Intercambiadores de calor (CDU de refrigeración líquida) | Uso industrial |
| 8413.70 / .81 | Bombas | Uso general |
| 8414.51 / .59 | Ventiladores | Uso general |

### Infraestructura física (solo sensibilidad en las series)
| SA6 | Qué registra | Cuidado |
|---|---|---|
| 9403.20 | Muebles de metal: racks y gabinetes | Posición genérica de muebles; en Argentina saltó en 2025 por la apertura de importaciones de muebles. Revisar el predecesor declarado |
| 7326.90 | Las demás manufacturas de hierro o acero | Muy genérica |

### Solo sensibilidad o indicativas
| SA6 | Qué registra | Por qué no entra en las series |
|---|---|---|
| 8542.31 / .32 | Procesadores y memorias (chips sueltos) | Van mayormente a ensamblaje, no a centros de datos |
| 8541 · 8528 | Semiconductores; monitores | Muy alejados del centro de datos |
| 2710.19 · 3403.99 · 3824.99 | Fluidos dieléctricos y de inmersión | No tienen línea propia: caen en «los demás» |

### Lo que la canasta deja afuera a propósito
- **8543.70**, máquinas eléctricas con función propia: según la práctica internacional (fallo HQ H309938 de la aduana de EE.UU.), allí van los **equipos de minería de criptomonedas**. No son computadoras programables y no forman parte del cómputo de la canasta.
- **8507.10**, baterías de arranque.

## Cómo registra cada país

La canasta común está a 6 dígitos porque es lo único que comparten todas las nomenclaturas. Cada país abre a su propio nivel, y **ahí es donde cambian las cosas**: qué subposición nacional recibe los aceleradores, cuándo entró en vigor cada enmienda, qué regímenes aduaneros quedan registrados.

| Nomenclatura | Países | Dígitos | A revisar |
|---|---|---|---|
| NCM (MERCOSUR) | Argentina, Brasil, Paraguay, Uruguay | 8 | La vigencia del SA2022 puede diferir por país (en Argentina, en la serie del INDEC desde 2024) |
| TIGIE + NICO | México | 8 + 2 | Regímenes temporales (IMMEX); ver abajo |
| Arancel nacional (base NANDINA) | Colombia, Perú, Ecuador, Bolivia | 10 | Subpartidas nacionales de 8471 y 8473. En Ecuador, economía dolarizada: el valor no requiere conversión cambiaria |
| Arancel de Aduanas de Cuba (base SA) | Cuba | verificar | Nivel de apertura y disponibilidad de la estadística por posición; ver abajo |
| SACH | Chile | 8 | Aperturas nacionales de 8471 |
| NC / TARIC | España (UE) | 8 / 10 | Estadística intracomunitaria (Intrastat) además de la extracomunitaria |

*Tabla de partida: cada equipo verifica y corrige la fila de su país con la fuente oficial, mediante un issue de «Clasificación arancelaria».*

## México: dónde buscar los aceleradores que en Argentina no vimos

En Argentina, el cómputo de IA entra mayormente como sistema completo y no aparece como acelerador suelto. En México el caso puede ser distinto, y conviene mirarlo con tres preguntas:

1. **¿En qué posición entran?** Un acelerador suelto (placa o módulo) va a 8473.30; un sistema acelerado completo, a 8471.41, 8471.49 u 8471.50. Revisar en la TIGIE y en los NICO qué apertura recibe cada uno.
2. **¿Entran para quedarse o para salir?** México ensambla equipamiento electrónico para exportar, en buena parte bajo programas de importación temporal (IMMEX). Una importación alta de aceleradores puede ser insumo de servidores que se reexportan, y no capacidad instalada en el país. Hay que verificar si la fuente estadística permite separar el **régimen definitivo** del **temporal**, y usar el definitivo para el método 5.
3. **¿Qué dice el espejo?** El cruce con las exportaciones de Estados Unidos y de Asia hacia México (método 4) muestra si el volumen es consistente con lo declarado, y la exportación mexicana de servidores muestra cuánto vuelve a salir.

Lo mismo vale para cualquier país con zonas francas o regímenes especiales. En Argentina, el área aduanera especial de Tierra del Fuego cumple un papel análogo para la electrónica de consumo: lo que se ensambla allí no se registra como importación de bien final.

## Cuba: cuando la fuente propia no alcanza

En Cuba, el método se invierte. Si la estadística oficial no publica las importaciones por posición arancelaria con el detalle necesario, o si la declaración del país a UN Comtrade es escasa o está desactualizada, el **cruce espejo deja de ser un control y pasa a ser la fuente principal**: lo que los socios declaran haber exportado a Cuba es la mejor aproximación disponible a lo que entró.

Tres cuidados:
1. **Verificar primero qué publica la fuente nacional** (la Oficina Nacional de Estadística e Información y la Aduana General de la República): nivel de apertura, años y si incluye valor y peso.
2. **Leer el espejo con sus límites**: el valor es FOB del exportador, la atribución de origen y la triangulación pesan más, y los envíos no comerciales quedan fuera.
3. **Tener en cuenta las restricciones de exportación**: el embargo de Estados Unidos alcanza al equipamiento informático de origen estadounidense, de modo que la procedencia declarada y el papel de los centros de reexpedición son, en sí mismos, un resultado a analizar.

El kit todavía no tiene un modo que use la suma de los socios como serie de importación: es una adaptación pendiente, que conviene plantear como issue cuando el equipo de Cuba confirme qué publica su fuente nacional.
