Instrucciones rápidas para la música de fondo

- Coloca tu archivo de música en el mismo directorio del proyecto con el nombre `megalovia.mp3`.
- El programa usa `pygame.mixer` para reproducir la pista de fondo en bucle. Instálalo con:

	pip install pygame

- Si `megalovia.mp3` no está presente, el juego seguirá funcionando sin música.
- Para sonidos cortos (efectos), el código intenta reproducir archivos mp3 con `pygame.mixer.Sound`.

Notas:
- En Windows PowerShell, ejecuta `python interfaz.py` desde este directorio para iniciar el juego.
- Si quieres reemplazar la pista, sustituye `megalovia.mp3` por otra canción del mismo nombre.
