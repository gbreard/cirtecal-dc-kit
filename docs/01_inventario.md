# 01 · Inventario de centros de datos

## Pregunta
¿Qué centros de datos hay en el país, dónde están, de qué tamaño son y cuáles se anuncian?

## Fuentes
- **Cámara del sector** (en Argentina, CABASE): cantidad y potencia agregada de los centros grandes. Sirve como referencia de cobertura.
- **Prensa especializada y general**: anuncios y proyectos.
- **Sitios de los operadores**: fuente primaria de existencia, dirección y potencia.
- **PeeringDB**: base pública y colaborativa donde las redes declaran los edificios en que tienen equipamiento. Útil para descubrir instalaciones y, en la ficha 02, para ver qué redes hay en cada una.
- **Registro de Uptime Institute**: certificaciones *Tier* por país.
- **Bases abiertas secundarias** (en Argentina, Tengo Data): solo como fuente de descubrimiento.
- **Registros institucionales**: regímenes de incentivo a la inversión, actos administrativos, licitaciones.

## Procedimiento
1. **Semilla.** Cargar lo que surge de la cámara y de la prensa.
2. **Candidatos.** Sumar los que aparecen en PeeringDB, Uptime y bases secundarias.
3. **Verificación.** Para cada candidato, buscar y leer la fuente primaria. Si no hay, el candidato queda en un archivo aparte con el motivo: sin fuente primaria, fuente inaccesible, fuente ilegible o fuente que no confirma.
4. **Campos obligatorios** (ver `plantillas/inventario.csv`): estado (operativo, anunciado), tipo de uso, potencia **con su base** (IT, total o no aclarada), coordenadas solo si la dirección es geocodificable, fuente, `descubierto_por` y si integra el conteo base.
5. **Duplicados.** Comparación aproximada de nombres y operadores, con revisión manual. El duplicado se conserva marcado y fuera del conteo.
6. **Tipo de uso**, por regla ordenada sobre el operador: público (Estado), transaccional (bancos y medios de pago), interconexión (alojamiento y telecomunicaciones), cómputo intensivo (por ejemplo, minería de criptomonedas) y, en los demás casos, corporativo o académico. Los anuncios de IA a escala llevan una etiqueta aparte, porque su uso es declarado y no observado.
7. **Cobertura.** Contar cuántos de los centros que reporta la cámara pueden auditarse con fuentes abiertas, y qué parte de su potencia.
8. **Congelar** el corte con una versión antes de usarlo.

## Trampas
- Una base secundaria no es un inventario: en Argentina, de 67 registros de Tengo Data, 12 entraron con fuente primaria y 34 quedaron como candidatos.
- PeeringDB dice que hay una instalación, no que sea un centro de datos: puede ser un nodo de red o una estación de amarre.
- Una certificación de diseño de Uptime no acredita que la instalación esté construida y operando.
- La potencia de una central asociada a un centro de datos no es su potencia de IT.
- Las direcciones que solo dan la ciudad terminan en el centroide: las distancias son aproximadas.

## Resultado en Argentina
41 registros: 31 centros operativos verificados y 8 anuncios. Solo 2 o 3 de los 13 centros de más de 1 MW que reporta la cámara pueden auditarse con fuentes abiertas (24–35% de la potencia). La opacidad es un resultado, no una limitación del relevamiento.

## En el kit
`kit/inventario.py` valida la planilla: campos obligatorios, base de la potencia, conteo base y cobertura frente a la cámara. Se corre con `python -m kit.inventario`.
