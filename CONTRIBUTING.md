# Cómo aportar al kit

El kit mejora con lo que encuentra cada equipo del consorcio. Hay dos formas de aportar.

## 1. Avisar (no hace falta saber git)
Abrir un *issue* en la pestaña **Issues** del repositorio y elegir la plantilla que corresponda:

- **Clasificación arancelaria**: una posición que registra equipamiento de centros de datos y el kit no mira, o una correspondencia entre enmiendas que falta o está mal.
- **Error en el kit**: un módulo que falla o da un resultado que no corresponde.
- **Trampa nueva**: algo que los hizo equivocar en su país y conviene que los demás sepan.

## 2. Proponer el cambio (con git)
Hacer un *fork*, modificar en una rama y abrir un *pull request*. Antes de enviarlo:

- correr `python -m pytest -q tests` y verificar que pasen;
- un cambio por pull request (por ejemplo, una correspondencia de la canasta o una ficha);
- si cambia una cifra del ejemplo argentino, explicar por qué.

Los pull requests los revisan los responsables del kit antes de incorporarlos.

## La regla que vale también para los aportes
**Todo cambio trae su fuente.** Una correspondencia arancelaria se respalda con la norma, el dictamen de clasificación o la tabla oficial (OMA, aduana nacional). Un dato del inventario, con la fuente primaria del operador u organismo. Sin fuente, el aporte queda como candidato hasta que se verifique.

## Qué no se sube
- Datos crudos de terceros con restricciones de licencia (PeeringDB, UN Comtrade): el kit los descarga.
- Claves, credenciales ni datos personales.

Las trampas aportadas por los países se suman a [docs/trampas.md](docs/trampas.md), indicando el país que las encontró.
