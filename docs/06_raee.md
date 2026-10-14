# 06 · RAEE de los centros de datos

## Pregunta
¿Cuánto residuo electrónico generan los centros de datos y cuándo?

## Fuentes
- Masa importada de la canasta de AEE estricta (ficha 03).
- Factor de atribución f (ficha 05).
- Vidas útiles por escenario (`config/parametros.yaml`).
- Referencias: Forti, Baldé y Kuehr (2018), directrices de estadísticas de RAEE; Baldé et al. (2024), Monitor Mundial de RAEE.

## Procedimiento
1. **Modelo de cohortes** (método de ventas y vida útil): W(t) = Σ M(t−k) · r(k), donde M es la masa importada cada año y r(k) la proporción que se da de baja k años después.
2. **Tres escenarios de vida útil**: corta (3–5 años), central (5–7) y larga (7–10, que ya incluye reúso), con bajas uniformes dentro de cada intervalo. Discretización anual: equivale a suponer importación y baja a mitad de año.
3. **Residuo de centros de datos**: W_CD(t) = f · W(t), con f calculado con el **mismo** escenario de vida útil. Las bandas propagan los escenarios a W y a f a la vez; no son intervalos de confianza.
4. **Proyección** con las cohortes ya importadas, sin agregar importaciones futuras. Es una referencia condicionada a los supuestos, no un mínimo garantizado.
5. **Segunda vida** (sensibilidad): una fracción q de lo retirado sigue en uso d años antes del descarte (q = 0, 25 y 50%; d = 1 y 2). No se aplica al escenario largo, que ya la incluye. Lo que se reacondiciona después de ser residuo no se descuenta.
6. **Baterías aparte**: plomo y litio, sin aplicarles f.
7. **Correspondencia con la Directiva 2012/19/UE**, para comparar entre países: los servidores en rack son categoría 4 (aparatos grandes); la exclusión de instalaciones fijas se evalúa equipo por equipo (artículo 2.4.c).

## Trampas
- r(k) representa el **retiro del primer uso** tratado como descarte en el mismo año. Si el retiro y el descarte difieren, hay que modelarlos por separado.
- Que el resultado no se mueva al corregir los datos de entrada no lo valida: en Argentina, el residuo total y f se movieron en sentidos opuestos y se compensaron en 2026, pero no en el escenario corto de 2027–2030.
- La segunda vida puede **subir** el residuo de una ventana: trae retiros altos de años anteriores.
- Las vidas útiles son escenarios exploratorios, no parámetros medidos en el país.

## Resultado en Argentina
En 2026, unas 3.100 t de RAEE del equipamiento IT del país, de las cuales unas 503 t corresponden a centros de datos de más de 1 MW (banda 321–573 t), cerca del 0,1% del RAEE nacional. Para 2027–2030, unas 1.500 t proyectadas desde cohortes ya importadas. Con segunda vida, hasta 645 t en 2026 y 1.969 t en 2027–2030.

## En el kit
`kit/raee.py`, con la variante de segunda vida. Se corre con `python -m kit.raee`.
