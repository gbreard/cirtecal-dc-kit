# 04 · Cruce espejo

## Pregunta
Lo que la aduana propia no muestra, ¿está oculto o solo mal atribuido?

## Fuentes
- **Aduana nacional**: importaciones por país de origen (CIF).
- **UN Comtrade**: exportaciones hacia el país declaradas por los socios (FOB). Requiere una clave gratuita, que el kit lee de una variable de entorno.

## Procedimiento
1. Elegir las partidas a 6 dígitos del SA: en Argentina, 8471.50 (servidores), 8473.30 (partes, donde se clasifican los aceleradores) y 8517.62 (conmutadores y enrutadores); 8543.70 como control.
2. Del lado nacional, sumar todas las subposiciones de cada partida.
3. Para cada celda producto × año × socio, calcular la brecha y el cociente espejo/nacional. Son indicadores de subregistro, no prueba de ocultamiento.
4. Clasificar cada celda por su causa probable:
   - **atribución de origen**: brecha fuerte con un socio, pero el total de la partida coincide;
   - **triangulación**: la brecha la declara un centro de reexpedición (Hong Kong, Irlanda, Países Bajos, Singapur);
   - **secreto probable**: el total de la partida falta (cociente ≥ 1,8) y la brecha con el socio es al menos diez veces;
   - **zona gris**: no puede separarse secreto de atribución;
   - **valuación**: brecha moderada, compatible con la diferencia FOB/CIF.
5. Probar la sensibilidad a los umbrales.
6. Nunca imputar: la serie nacional queda como cota inferior y el espejo se guarda aparte como evidencia.

## Trampas
- Cada aduana permite consultar una partida completa de forma distinta: el lado nacional del cruce no tiene implementación genérica.
- El crudo de Comtrade no se redistribuye: cada equipo lo baja con su clave.
- Antes de atribuir una brecha a una causa nueva, testearla. En Argentina se probó si la minería de criptomonedas explicaba parte de la brecha: sus equipos se clasifican en 8543.70, fuera de la canasta, y el secreto de 2023 venía de Estados Unidos y Europa, no de China.

## Resultado en Argentina
En 2023–2025 la brecha se explica sobre todo por atribución de origen (US$ 712 millones) y triangulación (US$ 223 millones). El secreto estadístico genuino es acotado: US$ 53–263 millones. La opacidad es de origen, no de volumen.

## Cuando la aduana propia no publica
Si la estadística nacional no tiene el detalle necesario (puede ser el caso de Cuba), el espejo se usa como fuente principal: lo que los socios declaran exportar al país es la mejor aproximación a lo que entró. Ver [canasta.md](canasta.md#cuba-cuando-la-fuente-propia-no-alcanza).

## En el kit
`kit/espejo.py` clasifica las celdas con los umbrales de la configuración. Antes hay que bajar los datos de Comtrade; si faltan, el módulo lo avisa. Se corre con `python -m kit.espejo`.
