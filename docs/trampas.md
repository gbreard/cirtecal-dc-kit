# Trampas encontradas en Argentina

Errores que cometimos o casi cometimos. Revisarlos antes de leer cualquier resultado propio.

## Aduana y nomenclatura
1. **La enmienda fabrica tendencias.** La enmienda 2022 del SA (vigente en la serie argentina desde 2024) renumeró posiciones de conmutadores, enrutadores, servidores y discos. La canasta tenía los códigos nuevos pero no los viejos, y la consulta devolvía vacío sin error. Resultado: un falso "máximo histórico" en 2025 y un falso "relevo del cómputo hacia la red". Control: empalmar, consultar a 8 dígitos y listar códigos vacíos después de cada carga.
2. **Códigos sin predecesor.** El control automático del kit marcó en Argentina 8471.70.40 (unidades de estado sólido, desde 2024) y 9403.20.90 (racks) sin empalme declarado. No leer un crecimiento en esas posiciones antes de resolverlo.
3. **Correspondencia 8473.30 → 8524.** Está cargada en la canasta común como "a verificar" contra la tabla oficial de la OMA.
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
