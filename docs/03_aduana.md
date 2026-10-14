# 03 · La huella en la aduana

## Pregunta
¿Entra por la aduana el equipamiento que la IA requiere? ¿Cuándo entró más?

## Fuentes
- **Aduana nacional**: importaciones por posición, año y origen, con valor CIF y kilos, al mayor nivel de detalle disponible.
- **Deflactor**: índice de precios al consumidor de Estados Unidos (CPI-U). Como sensibilidad, el índice de precios de importación de computadoras.

## Procedimiento
1. **Canasta por componentes** (explicada posición por posición en [canasta.md](canasta.md)). Ninguna posición "es de IA": la canasta se arma por capas (cómputo, red, almacenamiento, energía, refrigeración, estructura). La base común está a 6 dígitos del SA en `config/canasta_sa6.csv`; cada país la extiende a su nomenclatura nacional (ejemplo: `canasta_ar_ncm8.csv`).
2. **Dos canastas.** La de AEE estricta (cómputo, red y almacenamiento) alimenta el RAEE; la de inversión suma energía, refrigeración y estructura. Mezclarlas infla el residuo.
3. **Empalmar códigos** que cruzan enmiendas del SA: ningún código entra sin un predecesor identificado o una justificación de su creación.
4. **Control de códigos vacíos** después de cada carga: listar las posiciones sin registros en algún año.
5. **Deflactar** a dólares constantes y leer también en **toneladas**, que no necesitan deflactor.
6. **Composición**: qué parte del valor de cómputo entra como sistema completo y qué parte como acelerador suelto.

## Trampas
- **Enmienda 2022**: los códigos viejos no estaban en la canasta y la consulta a la aduana devolvía vacío sin error. Eso fabricó un "máximo histórico" en 2025 que no existía. Ver [trampas](trampas.md).
- **El cómputo de IA viaja escondido**: los aceleradores entran montados en sistemas completos (partida 8471) y la estadística no los distingue.
- La estructura física (racks, acero) usa posiciones genéricas que se mueven por otras razones; va solo como sensibilidad.
- La capa de energía es cota superior: sus posiciones incluyen uso industrial y residencial.

## Resultado en Argentina
El pico de la serie fue 2008–2011, en dólares constantes y en toneladas. 2025 ocupa el puesto 16 de 24 en valor y el 5º en peso. El 87% del cómputo importado en 2025 entró como sistema completo. El auge de la IA no pasa por la aduana.

## En el kit
`kit/aduana.py` arma la serie con la canasta, aplica empalmes, controla vacíos y deflacta. La consulta a la aduana se implementa en `kit/fuentes/aduana_plantilla.py`; `aduana_ar.py` es el ejemplo argentino. Se corre con `python -m kit.aduana`.
