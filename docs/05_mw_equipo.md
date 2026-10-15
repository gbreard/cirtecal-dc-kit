# 05 · De los megavatios al equipo

## Pregunta
¿Qué parte del equipamiento importado va a centros de datos? ¿Dejan huella los anuncios?

## Fuentes
- Potencia de IT del parque (en Argentina, la de la cámara del sector).
- Hojas técnicas de fabricantes: potencia y masa por servidor, densidad por rack.
- Costos de inversión por MW, desagregados por subsistema.
- La serie aduanera de la ficha 03.

Los coeficientes por MW, explicados como un cómputo métrico, están en [rendimientos_mw.md](rendimientos_mw.md).

## Procedimiento
1. **De la potencia al equipo.** Repartir la potencia de IT entre servidores de propósito general y sistemas acelerados (participación supuesta entre 0% y 15%) y calcular cantidad, masa y valor de servidores, almacenamiento y red. El equipamiento eléctrico y de refrigeración se dimensiona con la potencia total (PUE).
2. **Dos vías.** Física (hojas técnicas) y económica (costo por MW). Si convergen en el componente IT, el cálculo es consistente.
3. **Factor de atribución f.** Es el cociente entre la masa IT que el parque repone por año y la masa IT que importa el país por año, en una ventana de diez años. La reposición depende de la vida útil, que es el **mismo parámetro** del modelo de RAEE (ficha 06).
4. **Sensibilidad** de un parámetro por vez.
5. **Anuncios.** Calcular el equipo que requeriría un proyecto anunciado y compararlo, en valor, con todo lo importado en el período.

## Trampas
- La base de la potencia pesa más que cualquier otro supuesto: en Argentina, si la cifra de la cámara fuera potencia total en vez de IT, f bajaría un 36%.
- La comparación con los anuncios se hace en valor, no en peso: un sistema acelerado concentra mucho valor en poca masa, y en toneladas el resultado sería absurdo.
- f es un promedio fijo de la ventana; calcularlo con una ventana móvil que acompañe a las cohortes es una revisión pendiente.

## Resultado en Argentina
Los centros de datos explican cerca de un sexto del equipamiento IT importado: f = 0,163 (banda 0,109–0,233), y menos del 2% del equipamiento eléctrico y de refrigeración. Todo el cómputo importado entre enero de 2025 y agosto de 2026 alcanzaría para equipar unos 14 MW, el 3% del mayor proyecto anunciado (500 MW).

## En el kit
`kit/mwbom.py`, con los parámetros y sus fuentes en `config/parametros.yaml`. Se corre con `python -m kit.mwbom`.
