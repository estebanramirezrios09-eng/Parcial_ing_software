# La última transmisión — motor de historias interactivas

Parcial práctico de Ingeniería de Software · versión del motor: **1.1.0** (1.0.0 + deshacer la última decisión)

**Integrantes:** Esteban Ramírez Rios y Emmanuel David Angulo

Motor de consola que interpreta narraciones descritas en archivos JSON: muestra la escena actual, ofrece solo
las opciones compatibles con lo ocurrido, aplica consecuencias, detecta finales y rechaza contenido inválido
con mensajes que indican qué corregir. Las historias se cambian **sin tocar el código**.

## Versiones requeridas

- Python 3.9 o superior (verificado en Windows con Python 3.14.3).
- Para las pruebas: `pytest` (licencia MIT). El motor solo usa la biblioteca estándar.

## Instalación

Desde la raíz de este repositorio, en PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\Activate.ps1
```

En Linux/macOS, activar con `source .venv/bin/activate` e instalar con
`python -m pip install -r requirements.txt`.

## Ejecución

```bash
python -m transmision                                   # historia principal, partida interactiva
python -m transmision historias/el_faro.json            # segunda historia, mismo motor
python -m transmision historias/el_faro.json --validar  # solo validar el archivo
python -m transmision --ruta revisar,investigar,activar_codigo   # reproduce un recorrido
python -m transmision --ruta "revisar,investigar,@deshacer,continuar"   # '@deshacer' retrocede una decisión
```

En la partida interactiva se escribe el **número** de la opción mostrada; `u` deshace la última decisión, `r` reinicia, `q` sale. Al llegar a un
final (o a un bloqueo) se ofrece jugar de nuevo. Código de salida: `0` correcto, `1` recorrido que no llega a un
final, `2` historia inválida o inexistente.

## Pruebas

```bash
python -m pytest pruebas -v                # 103 pruebas automatizadas (U1-U6, I1, CA01-CA03, RNF)
python pruebas/verificar_rnf.py            # verificación completa de los 3 RNF -> resultados/rnf.txt
```

Los registros de la última ejecución están en `resultados/pruebas.txt` y `resultados/rnf.txt`.

## Rutas para demostrar cada final

| Final | Recorrido (IDs de opción) | Qué muestra |
|---|---|---|
| E4 Rescate | `revisar,investigar,activar_codigo` | Investigar habilita «Activar con código» |
| E5 El eco | `revisar,continuar,activar_sin_verificar` | Sin investigar solo existe «Activar sin verificar» |
| E6 Silencio | `revisar,continuar,cortar` | «Cortar comunicación» está siempre disponible |

Error de contenido (CA03): `python -m transmision historias/invalidas/destino_inexistente.json`

## Formato de contenido (JSON)

```json
{
  "titulo": "Nombre de la historia",
  "inicio": "ID de la escena inicial",
  "variables": {"conoce_origen": false},
  "escenas": [
    {
      "id": "E2", "texto": "Texto visible", "final": false,
      "opciones": [
        {"id": "investigar", "texto": "Investigar archivo", "destino": "E3",
         "condiciones": {}, "efectos": {"conoce_origen": true}}
      ]
    }
  ]
}
```

- `variables`: estado inicial de cada partida; **solo booleanos**. Toda variable usada debe estar declarada aquí.
- `condiciones`: mapa `variable: valor`; la opción se muestra solo si **todas** se cumplen. `{}` = siempre visible.
- `efectos`: mapa `variable: valor` que se asigna al elegir. `{}` = no cambia nada.
- Escena `final: true` → `opciones` vacía. Escena `final: false` → al menos una opción.
- IDs de escena únicos; IDs de opción únicos dentro de su escena; `destino` e `inicio` deben existir.
- **Todos los campos del contrato son obligatorios** (incluidos `condiciones` y `efectos`, aunque estén vacíos).

Equivalencia con el contrato de la guía: es el mismo contrato sin cambios de nombres ni significado.

Códigos de error de validación: `E_ILEGIBLE`, `E_ESTRUCTURA`, `E_CAMPO_AUSENTE`, `E_INICIO`, `E_ESCENA_DUP`,
`E_OPCION_DUP`, `E_DESTINO`, `E_VARIABLE`, `E_NO_BOOL`, `E_FINAL_OPCIONES`. Cada mensaje incluye la causa y el
campo o ID involucrado, y se informan todos los problemas encontrados de una vez.

## Estructura del proyecto

```
transmision/   modelos.py, reglas.py        dominio (sin entrada/salida)
               diagnostico.py, validador.py, cargador.py   contenido
               sesion.py                    estado de la partida
               consola.py                   interfaz
historias/     la_ultima_transmision.json, el_faro.json (2.ª historia), invalidas/
pruebas/       pruebas automatizadas y verificar_rnf.py
resultados/    registros de ejecución
docs/          informe.pdf, anexo.pdf, diagramas, gestion_cambio.md, generadores (opcionales)
evidencia/     backlog.csv, historial_git.txt, versiones.md
```

El historial exportado corresponde a este repositorio. `evidencia/versiones.md` identifica la versión
con retroceso y explica la ausencia de una versión ejecutable anterior en el historial disponible.
Los guiones de grabación se conservan fuera del repositorio.

## Decisiones y acuerdos provisionales

- **Retroceso (cambio de la hora 6, v1.1.0):** el cliente decidió que el lector pueda deshacer su última decisión, lo que
  reemplaza el acuerdo provisional de v1.0.0 (sin retroceso). Reglas: deshacer restaura la escena, las variables y el historial
  previos a la última elección válida; es de **un solo nivel** (no hay otro retroceso hasta una nueva elección válida) y no hay
  rehacer; al comenzar o tras reiniciar no hay retroceso disponible; una opción inexistente o no habilitada no modifica la
  sesión ni sustituye lo que se deshará; se puede deshacer desde E4, E5 o E6 (se regresa a E3). Requisitos RF-19 a RF-22 en el informe.
- El motor acepta tanto el número visible como el ID de la opción; el ID de una opción no habilitada se rechaza
  siempre (CA02).

## Limitaciones conocidas

- No se analizan automáticamente todos los caminos posibles del relato (alcanzabilidad de finales, ciclos); un
  bloqueo se detecta y se informa durante la partida.
- No hay guardado entre ejecuciones, cuentas, audio ni imágenes (fuera del alcance).
- Una historia con identificadores o textos muy extensos no se ha probado más allá de las dos historias incluidas.
- Los IDs de opción de `la_ultima_transmision.json` coinciden con el archivo oficial del docente;
  si cambian, se ajustan las constantes de `pruebas/conftest.py`.
- Las herramientas para regenerar los PDF (`docs/generar_*.py`) requieren `reportlab`, `pypdf`, `Pillow`,
  `matplotlib` y el ejecutable `dot` de Graphviz; no son dependencias del motor. El generador de documentos
  busca las fuentes DejaVu en `%SystemDrive%\ttf` (Windows) o `/usr/share/fonts/truetype/dejavu` (Linux).
