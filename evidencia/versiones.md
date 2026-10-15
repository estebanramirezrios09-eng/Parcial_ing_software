# Versiones y alcance de la evidencia de Git

Repositorio: https://github.com/emangulo112w/Parcial_ing_software

## Versión posterior al cambio: v1.1.0

El commit `2fa3133` (14 de octubre de 2026, 20:18:53 -05:00), titulado
«Motor v1.1.0: deshacer la última decisión», incorpora el motor completo con retroceso,
las pruebas U6 y las ampliaciones de U5 e I1. El código declara la versión `1.1.0`
en `transmision/__init__.py`. La etiqueta `v1.1.0` identifica ese commit.

Los commits posteriores incorporan correcciones de documentación, identificación de ambos integrantes,
restauración de diagramas, resultados de verificación y limpieza de archivos. No cambian las reglas del motor.

## Versión previa declarada: v1.0.0

El informe y la gestión del cambio describen una versión sin retroceso denominada `v1.0.0`.
Sin embargo, el historial disponible de este repositorio no conserva un motor ejecutable previo:
antes de `2fa3133` solo contiene el README y archivos de documentación. El commit `a3e2705`,
aunque se titula «Implementar funcionalidad de deshacer decisión», modifica únicamente un documento.

El antiguo historial exportado citaba los identificadores `41bfb30`, `d608162`, `39ca324` y `f5a98ac`;
estos objetos no están presentes en el repositorio recuperado. Por ello se sustituyó esa exportación
por una obtenida del Git real y no se creó una etiqueta `v1.0.0` sobre una versión distinta.

La evidencia de la versión ejecutable anterior al cambio queda pendiente de recuperar desde una
copia o repositorio original, si existe. Su descripción en el informe no sustituye esa evidencia.

## Verificación y exportación

- Código actual: 103 pruebas automatizadas y tres requisitos no funcionales verificados.
- Registros reproducibles: `resultados/pruebas.txt` y `resultados/rnf.txt`.
- Historial con autores, fechas y mensajes: `evidencia/historial_git.txt`.
- La exportación indica el commit hasta el que fue tomada; el commit que guarda el propio archivo
  se registra después de generar la exportación.
