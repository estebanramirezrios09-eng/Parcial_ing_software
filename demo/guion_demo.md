# Guion de la demostración (máximo 6 minutos, MP4, Esteban Ramírez Rios)

Preparar: terminal con letra grande (≥ 16 pt), carpeta del proyecto abierta, entorno virtual activo.
Sin cámara. Se puede narrar con voz o con rótulos. Esteban Ramírez Rios presenta todos los bloques.

| Min | Bloque | Comando / acción | Qué debe verse |
|---|---|---|---|
| 0:00 | Presentación | Mostrar README y nombres | Integrantes y versión del motor |
| 0:20 | Final E4 | `python -m transmision --ruta revisar,investigar,activar_codigo` | En E3 solo «Activar con código» y «Cortar comunicación» |
| 1:00 | Final E5 | `python -m transmision --ruta revisar,continuar,activar_sin_verificar` | En E3 ahora aparece «Activar sin verificar» (condición cambia las opciones) |
| 1:35 | Final E6 | `python -m transmision --ruta revisar,continuar,cortar` | Tercer final |
| 2:00 | Entrada inválida | Partida interactiva: escribir `abc`, `9`; luego en E3 sin investigar escribir `activar_codigo` | «Entrada no válida», la escena no cambia (CA02) |
| 2:40 | Reinicio | Llegar a un final y responder `s` | Nueva partida sin rastro de la anterior |
| 3:05 | Segunda historia | `python -m transmision historias/el_faro.json` | Mismo motor, otra historia, sin editar código |
| 3:45 | Error de contenido | `python -m transmision historias/invalidas/destino_inexistente.json` | Mensaje `E_DESTINO` con `E99` y el campo; no se abre partida (CA03) |
| 4:15 | Pruebas | `python -m pytest pruebas -q` y `python pruebas/verificar_rnf.py` | Todo en verde, 3 RNF cumplen |
| 4:45 | Cambio de la fase 2 | Mostrar el comportamiento solicitado (completar tras la hora 6) | Funcionando + su prueba |
| 5:25 | Arquitectura e impacto | Mostrar `docs/diagramas/06_componentes.png` | Decisión: contenido declarativo separado de motor e interfaz; qué archivos tocó el cambio |
| 5:50 | Cierre | | Fin |

Subir el MP4 al ZIP o enlazarlo en el README con acceso para el docente (probar el enlace en una ventana privada).
