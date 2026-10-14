# 02 · Localización y uso del parque

## Preguntas
¿Los centros de datos se ubican junto a los cables submarinos, junto a los nodos de intercambio de tráfico o junto a la energía? ¿Para qué se usa el parque instalado?

## Fuentes
- **Estaciones de amarre**: OpenStreetMap; cables en servicio según operadores y reguladores. Las bases comerciales de cables tienen restricciones de licencia y no se usan como fuente de datos.
- **Sedes de intercambio de tráfico**: PeeringDB.
- **Redes presentes en cada instalación**: PeeringDB (redes que declaran estar en cada edificio y sus datos).

## Procedimiento: localización
1. Para cada centro con coordenadas, calcular la distancia en línea recta a la estación de amarre más cercana, a la sede de intercambio más cercana y al **nodo principal** de intercambio del país.
2. Clasificar por lógica de localización:
   - **conectividad**: a menos de 50 km del nodo principal;
   - **energética**: fuera de ese umbral, y la fuente primaria declara una motivación energética (columna `motivacion_energetica_fuente` del inventario);
   - **mixta**: los demás casos;
   - sin coordenadas: no se clasifica.
3. Probar la sensibilidad al umbral (`localizacion.umbral_nodo_km` en `config/parametros.yaml`) e informar qué casos cambian.
4. La distancia al amarre se informa como dato del país y no se usa para clasificar: la capacidad de los cables se entrega en puntos de presencia tierra adentro.

## Procedimiento: uso
1. Para cada centro registrado en PeeringDB, bajar la lista de redes presentes.
2. Marcar las plataformas de contenido y nube extranjeras con una lista explícita, revisada a mano red por red.
3. Informar cuántos centros de interconexión alojan esas plataformas. Es una **cota inferior**: las cachés instaladas dentro de las redes de los proveedores de acceso no se declaran en un edificio.

## Trampas
- Tener un punto de intercambio cerca no discrimina: la red de CABASE tiene 29 sedes en Argentina, y los centros siguen en el AMBA.
- La lista de plataformas extranjeras es manual y depende del país: el kit no la trae y cada equipo arma la suya.

## Resultado en Argentina
12 de los 14 centros operativos con coordenadas están a menos de 36 km del nodo principal, y el único amarre del país está a 257 km. Los anuncios con ubicación conocida están a más de 570 km, junto a la generación. En 4 de los 6 centros de interconexión registrados hay nodos de plataformas extranjeras: el parque funciona como puerta de entrada de servicios producidos afuera.

## En el kit
`kit/localizacion.py` calcula distancias y clasifica; el nodo principal y los amarres van en `config/pais.yaml` y el umbral, en `config/parametros.yaml`. Se corre con `python -m kit.localizacion`.
