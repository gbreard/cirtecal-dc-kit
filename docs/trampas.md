# Trampas encontradas en Argentina

Errores que cometimos o casi cometimos. Revisarlos antes de leer cualquier resultado propio.

## Aduana y nomenclatura
1. **La enmienda fabrica tendencias.** La enmienda 2022 del SA (vigente en la serie argentina desde 2024) renumeró posiciones de conmutadores, enrutadores, servidores y discos. La canasta tenía los códigos nuevos pero no los viejos, y la consulta devolvía vacío sin error. Resultado: un falso "máximo histórico" en 2025 y un falso "relevo del cómputo hacia la red". Control: empalmar, consultar a 8 dígitos y listar códigos vacíos después de cada carga.
2. **Códigos sin predecesor.** El control automático del kit marcó en Argentina 8471.70.40 (unidades de estado sólido, desde 2024) y 9403.20.90 (racks) sin empalme declarado. Resuelto (15-oct-2026), los dos con fuente primaria:
   - **SSD, 8471.70.40.** Lo creó la NCM de la VII Enmienda (Res. GMC 16/21, vigente en la serie del INDEC desde 2024-01) y viene entero de **8471.70.90** ("unidades de memoria ncop"), que sigue vigente. No viene de 8471.70.12 (discos rígidos magnéticos), que pasó a 8471.70.10. Fuentes: tabla de correlación NCM 2017–2022 de la DNIT de Paraguay, fila 8471.70.90 → 8471.70.40 y ex 8471.70.90; glosas del INDEC (8471.70.40 solo existe en la enmienda 7; 8471.70.90 existe en las enmiendas 3 a 7). La OMA no lo registra porque a 6 dígitos no cambió nada.
     - Es una **partición, no una fusión**: el código viejo sigue vivo. Por eso se declara como enlace parcial, `sucesor_empalme = ex 8471.70.40` en la fila de 8471.70.90, y la serie se lee como la suma de los dos.
     - Lo que parecía un nacimiento de US$65M en 2024 es una mudanza: 8471.70.90 cae de US$82,0M (2023) a 22,1M (2024). La suma .40 + .90 pasa de US$82,0M a 87,3M (+6 %), y de 172 t a 206 t.
   - **Racks, 9403.20.90.** Su predecesor es **9403.20.00**, que la Res. GMC 19/22 (Anexo) partió en 9403.20.10 (muebles de cocina, fuera de la canasta) y 9403.20.90 (los demás). Argentina la adoptó con el Decreto 384/2024 (art. 1, BO 06/05/2024); de ahí el quiebre en 2024-05 y no en 2024-01. Hasta 2024-04 la serie incluye los muebles de cocina: 45 t en mayo–diciembre de 2024 y 226 t en 2025 (INDEC, 9403.20.10), entre el 1 % y el 1,5 % del peso de 9403.20.90. La serie no se corrige por eso.
   - **Las cifras no se mueven.** Las dos parejas ya estaban en la canasta y las series por capa suman todos los códigos: la serie por capa, f y el RAEE salen idénticos. Cambian la columna `codigo_empalmado` y el control, que ya no marca `sin_empalme` en estos dos códigos (de 13 a 11 marcas `sin_empalme`; siguen con `nace_en_enmienda`, que es informativo).
3. **Correspondencia 8473.30 → 8524.** Verificada (15-oct-2026) contra la tabla oficial de la OMA: *Correlation Tables HS 2017–2022* (noviembre de 2020), Tabla I, p. I/27 (8524.11 a 8524.99, y 8529.90) y Tabla II, pp. II/18–19.
   - **Qué pasó a 8524:** solo los módulos de visualización de pantalla plana (nueva Nota 7 del capítulo 85). La OMA lista la partida 84.73 entre los orígenes posibles, sin bajar a subpartida. En la NCM baja: 8473.30.92 (pantallas para portátiles) → ex 8524.91 / .92 / .99 (tabla de correlación NCM 2017–2022, DNIT Paraguay).
   - **Qué queda en 8473.30:** todo lo demás. El texto de la subpartida no cambió: placas con componentes, aceleradores, memorias y demás partes de 8471 siguen ahí. 8473.30.99 pasa entera a 8473.30.90.
   - **Efecto en Argentina:** ninguno. 8473.30.92 nunca estuvo en la canasta. Se quitó la marca "a verificar" de `canasta_sa6.csv`; la correspondencia queda como parcial (`parte (ex) → 8524`).
4. **Baterías.** Los acumuladores de plomo para arranque de motores son 8507.10; 8507.20 son los demás acumuladores de plomo y 8507.60, los de litio. La canasta no incluye 8507.10.
5. **Equipos de minería de criptomonedas.** La práctica internacional los clasifica en 8543.70, fuera de la partida de computadoras: no forman parte de la canasta ni del factor de atribución.
6. **El acelerador viaja dentro del sistema.** El cómputo de IA entra mayormente como sistema completo (8471), no como placa suelta.

## Inventario
7. **Las bases secundarias no son inventarios.** Usarlas para descubrir, nunca para cargar sin fuente primaria.
8. **PeeringDB no dice qué es un edificio.** Una instalación puede ser un nodo de red o un amarre.
9. **Certificación de diseño no es operación.**
10. **Generación no es potencia de IT.** La potencia de la central que abastece un centro no se carga como su capacidad.
11. **La base de la potencia importa.** IT, total o no aclarada: nunca se suman cifras con bases distintas.
12. **Centroides.** Una dirección que solo da la ciudad no es una coordenada.

## Modelo
13. **La compensación no es validación.** Que el resultado final no cambie al corregir los datos puede deberse a que dos componentes se mueven en sentidos opuestos.
14. **Retiro no es descarte.** Definir qué evento representa la vida útil antes de interpretar el residuo.
15. **Redondeos.** Usar el mismo valor de f, sin redondear, en todas las cifras derivadas (en Argentina, 503 t y 1.500 t, no 504 y 1.501).

## Aportadas por los equipos país
Cada trampa nueva se suma acá con el país que la encontró y el *issue* donde se discutió (ver [CONTRIBUTING.md](../CONTRIBUTING.md)).
