# Fichas de método

Cada ficha explica un método del kit: qué pregunta responde, con qué fuentes, cómo se procede, qué trampas encontramos en Argentina y qué resultado produce. El código que lo implementa está indicado al final de cada una.

| Ficha | Pregunta | Módulo |
|---|---|---|
| [00 · Diseño](00_diseno.md) | ¿Cómo se combinan fuentes que no comparten datos? | — |
| [01 · Inventario](01_inventario.md) | ¿Qué centros de datos hay, dónde y de qué tamaño? | `kit/inventario.py` |
| [02 · Localización y uso](02_localizacion.md) | ¿Junto a qué se ubican y para qué se usan? | `kit/localizacion.py` |
| [03 · Aduana](03_aduana.md) | ¿Entra por la aduana el equipamiento que la IA requiere? | `kit/aduana.py` |
| [La canasta](canasta.md) | ¿Qué posiciones arancelarias miramos, por qué y cómo cambian por país? | `config/canasta_sa6.csv` |
| [04 · Espejo](04_espejo.md) | ¿Lo que no se ve en la aduana está oculto o mal atribuido? | `kit/espejo.py` |
| [05 · De los MW al equipo](05_mw_equipo.md) | ¿Qué parte de lo importado va a centros de datos? | `kit/mwbom.py` |
| [Rendimientos por MW](rendimientos_mw.md) | ¿Cuánto equipo, peso y valor lleva un MW de IT? | `config/parametros.yaml` |
| [06 · RAEE](06_raee.md) | ¿Cuánto residuo generan y cuándo? | `kit/raee.py` |
| [Trampas](trampas.md) | Lo que nos hizo equivocar, para que no les pase | — |

La clase de método con la que se presentó el kit está en [`clase/`](../clase/).

Orden sugerido para replicar: 00 → 01 → 02 → 03 → 04 → 05 → 06. Los métodos 05 y 06 necesitan los resultados de 01 y 03.

Referencia de resultados: Llorente, L. J. y Breard, G. E. (2026). *Centros de datos para inteligencia artificial en Argentina. Infraestructura, importación de equipamiento y generación de RAEE*. Informe país CIRTECAL, octubre de 2026.
