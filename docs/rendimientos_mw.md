# Rendimientos por MW: el cómputo métrico de un centro de datos

Un arquitecto sabe cuántos ladrillos, cuánto cemento y cuántas horas de oficial lleva un metro cuadrado de pared. Para un centro de datos la lógica es la misma: a partir de la potencia de IT se puede estimar cuánto equipo de cómputo, refrigeración y energía necesita, cuánto pesa y cuánto cuesta. Esta ficha reúne esos rendimientos para **1 MW de potencia de IT**, con los coeficientes de [`config/parametros.yaml`](../config/parametros.yaml), donde cada valor lleva su fuente y su estado (verificado, parcial o supuesto).

Es la tabla que usa el método 5 ([05_mw_equipo.md](05_mw_equipo.md)). Las cifras de esta página son **aritmética directa sobre esos parámetros**, para mostrar órdenes de magnitud; las cifras del informe salen de correr `python -m kit.mwbom`, que además propaga bandas y vidas útiles.

## Dos perfiles de centro de datos

| | Convencional | De IA |
|---|---|---|
| PUE (potencia total / potencia de IT) | 1,55 (promedio mundial, Uptime Institute) | 1,2 (hiperescala eficiente: 1,08–1,2) |
| Potencia por rack | 4–10 kW (promedio ~5 kW) | 40–132 kW |
| Parte de los servidores con aceleradores (GPU) | 0–15% (supuesto) | 95% (supuesto) |
| Redundancia | N+1 | N+1 |
| Baterías | Plomo | Litio |

## Rendimientos por MW de IT

Cómo se reparte el MW de IT (IEA, 2025): ~857 kW en servidores, ~71 kW en almacenamiento y ~71 kW en red.

### Cómputo, almacenamiento y red
| Componente | Convencional | De IA | Coeficiente usado |
|---|---|---|---|
| GPU | 0–100 | **~450–640** | DGX B200: 14,3 kW con 8 GPU; GB200 NVL72: 132 kW con 72; DGX H100: 10,2 kW con 8 |
| Servidores sin aceleradores | ~1.800–2.100 | ~110 | 0,4 kW por servidor (Dell R760) |
| Equipos de almacenamiento | ~58 | ~58 | 1,23 kW por unidad (NetApp AFF A400) |
| Conmutadores de red | ~76 | ~76 | 0,94 kW (NVIDIA Spectrum SN5600) |
| Racks | 100–250 | 8–25 | Potencia por rack del perfil |
| **Masa del equipo IT** | **61–69 t** | **16–18 t** | Masa de cada equipo según su ficha |
| Masa de los racks vacíos | 13–34 t | 1–3 t | 134 kg por rack (APC AR3300) |
| **Valor del equipo IT** | **~US$ 27 millones** | **~US$ 25–35 millones** | Precios de lista o de revendedores (estado: parcial o supuesto) |

### Energía y refrigeración
| Componente | Convencional | De IA | Regla |
|---|---|---|---|
| Potencia total de la instalación | 1,55 MW | 1,2 MW | IT × PUE |
| Calor a evacuar | ~1 MW térmico (~285 TR) | ~1 MW térmico (~285 TR) | Todo lo que consume el IT se vuelve calor (1 TR = 3,517 kW) |
| Capacidad de enfriamiento | 1,25 MW · chillers ~10 t | 1,25 MW · chillers ~10 t | IT × redundancia; chiller 8,2 kg/kW (Carrier 30XA) |
| UPS | 1,25 MW · ~3,9 t | 1,25 MW · ~3,9 t | IT × redundancia; 3,1 kg/kW (Liebert, Galaxy) |
| Baterías (10 minutos) | ~210 kWh · ~10 t de plomo | ~210 kWh · ~3 t de litio | UPS × autonomía; plomo 50 kg/kWh, litio 15 kg/kWh |
| Grupos electrógenos | ~1,9 MW · ~15,5 t | 1,5 MW · ~12 t | Total × redundancia; 8 kg/kW (Cat 3516C) |
| Transformadores | ~2,2 MVA · ~5,2 t | ~1,7 MVA · ~4 t | Total / factor de potencia × redundancia; 2,4 kg/kVA |

### Inversión
| | Convencional | De IA |
|---|---|---|
| Obra e instalaciones, sin el IT | ~US$ 12,5 millones por MW (consultoras inmobiliarias, 2025–2026) | — |
| Total con el IT | ~US$ 40 millones por MW (obra + IT) | ~US$ 38 millones por MW (Epoch AI, 2026) |

## Lo que la tabla enseña

- **Un MW de IA pesa mucho menos y vale lo mismo o más.** Por MW, un centro convencional tiene unas 65 toneladas de equipo IT; uno de IA, menos de 20. El valor por tonelada se multiplica por cuatro. Por eso la comparación entre lo anunciado y lo importado se hace en valor y no en peso (método 5), y por eso un centro de IA genera menos residuo IT por MW, aunque lo renueva más rápido (método 6).
- **El equipo eléctrico y de refrigeración pesa tanto como el IT.** En un centro de IA, grupos, chillers, UPS, baterías y transformadores suman unas 33 toneladas por MW, el doble que el IT. Ese equipo dura más, pero también se vuelve residuo.
- **La refrigeración se dimensiona por el calor, no por el tipo de centro.** Un MW de IT es un MW de calor, sea de IA o no. Cambia la forma de evacuarlo (aire o líquido), no la cantidad.

## Por qué no es tan estable como un cómputo de albañilería

1. **La receta envejece en uno o dos años.** De la generación H100 a la B200 casi se duplicó la potencia por GPU y por rack. Cada coeficiente necesita la fecha y la generación de equipo: los de esta página son de octubre de 2026.
2. **Depende del diseño.** Refrigeración por aire o por líquido, redundancia N+1 o 2N, baterías de plomo o de litio: cada decisión cambia los rendimientos. Por eso el kit trabaja con escenarios (bajo, central y alto) y no con un número.
3. **No hay un manual público.** Fabricantes y diseñadores tienen estas tablas en sus herramientas de diseño, pero no las publican como tales. Esta ficha las reconstruye a partir de fichas técnicas y documentos públicos, y cada coeficiente se puede reemplazar por uno mejor documentado (ver [CONTRIBUTING.md](../CONTRIBUTING.md)).

## Para usarla en otro país
Los rendimientos no dependen del país, salvo el PUE, que varía con el clima (refrigerar en Neuquén no cuesta lo mismo que en Guayaquil), y los precios, que cambian con aranceles y tipo de cambio. Lo que cada equipo aporta es la potencia: la que informa la cámara del sector o la que surge de su inventario (método 1).
