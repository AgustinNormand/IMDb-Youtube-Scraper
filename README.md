# Jordan-Scrapper

Low level documentation available in Colab, the perpose of this file is high/mid level documentation.

Empecé a hacer unas primeras pruebas usando Python, concretamente, en Google Colab, debido a que es interactivo, tiene una buena interracion entre codigo, resultados y documentación. No necesariamente este va a ser la herramienta final a utilizar.

## Box Office Mojo Scrapper

### Old API alternatives

Busqué librerías existentes para hacer la tarea sin reinventar la rueda.
El primer resultado en google es https://github.com/lamlamngo/Box-Office-Mojo-API una API cuyo ultimo commit fué en 2018, de tan solo 11 comits.
No tiene mantenimiento actual, probablemente tenga cosas que ya no funcionen.

En PyPi, hay disponible una librería https://pypi.org/project/BoxOfficeMojo/ cuyo nombre y versión es BoxOfficeMojo 0.0.9, la versión mas reciente es de 20 de diciembre de 2014, por los mismos motivos que la anterior, no la usaría.

Buscando más, sin encontrar demasiado, concluyo que no hay librerias que faciliten el trabajo de scrapear este sitio, por lo que empiezo a hacer mi versión del scrapper.

### Fake Headers 

Usé la librería fake_headers de Python para inventar headers y engañar al servidor HTTP, para no evidenciar que es un script y asi evitar baneos.

### Offset parameter

Los botones de siguiente y anterior, funcionan agregando un offset en el query string.
![image](https://user-images.githubusercontent.com/48933518/203129568-2362ddde-3d26-4d72-8bd9-486fcff9698f.png)

Cuando clickeamos next, lo incrementa en 200 (ya que comienza en 0), por lo que se van a necesitar 5 peticiones para obtener los 1000 resultados iniciales.
![image](https://user-images.githubusercontent.com/48933518/203129673-e4f1a567-937e-4df0-9f7e-1d2f24846d36.png)

### <tr> in body

In the body of the html of Box Office Mojo:
![image](https://user-images.githubusercontent.com/48933518/203125818-14dfbbc7-f174-49d0-b1a3-0f6a9c4febaa.png)

The first <tr>, the one that has style="display none" wich means is hidden, contains info non relevant, non movies, its important to ignore it.
![image](https://user-images.githubusercontent.com/48933518/203126000-4611297e-257b-4aed-b326-1eb0cc76ce98.png)

The one that corresponds to the first movie, is instead, the second one <tr> in the <tbody>
![image](https://user-images.githubusercontent.com/48933518/203127371-6bdeb37d-94e5-4f90-8a60-1d4da7787596.png)

### Time wait between requests
