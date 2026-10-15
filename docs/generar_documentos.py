"""Genera docs/informe.pdf (cuerpo) y docs/anexo.pdf (diagramas, matriz, tablero).
Uso (desde la raíz):  python docs/generar_documentos.py
Requiere reportlab y haber ejecutado antes docs/generar_diagramas.py y las pruebas."""
import os
import pathlib
import re
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

RAIZ = pathlib.Path(__file__).resolve().parent.parent
DIAG = RAIZ / "docs" / "diagramas"
if sys.platform == "win32":
    FUENTES = pathlib.Path(os.environ.get("SystemDrive", "C:") + "/") / "ttf"
elif sys.platform.startswith("linux"):
    FUENTES = pathlib.Path("/usr/share/fonts/truetype/dejavu")
else:
    sys.exit(f"Plataforma no contemplada para las fuentes: {sys.platform}")
for nombre, archivo in (("DV", "DejaVuSansCondensed.ttf"), ("DV-B", "DejaVuSansCondensed-Bold.ttf"),
                        ("DV-I", "DejaVuSansCondensed-Oblique.ttf"), ("DV-M", "DejaVuSansMono.ttf")):
    pdfmetrics.registerFont(TTFont(nombre, str(FUENTES / archivo)))
pdfmetrics.registerFontFamily("DV", normal="DV", bold="DV-B", italic="DV-I", boldItalic="DV-B")

AZUL = colors.HexColor("#2f4a78")
GRIS = colors.HexColor("#f1f3f7")

# ------------------------------------------------------------ datos reales de ejecución
def leer(ruta):
    p = RAIZ / ruta
    if not p.exists():
        sys.exit(f"Falta {ruta}: ejecute primero las pruebas (ver README).")
    return p.read_text(encoding="utf-8")


pruebas_txt = leer("resultados/pruebas.txt")
rnf_txt = leer("resultados/rnf.txt")
m = re.search(r"(\d+) passed", pruebas_txt)
if not m or "failed" in pruebas_txt.splitlines()[-1]:
    sys.exit("resultados/pruebas.txt no muestra una ejecución limpia; no se genera el informe.")
N_PRUEBAS = int(m.group(1))
if "3/3 RNF cumplen" not in rnf_txt:
    sys.exit("resultados/rnf.txt no muestra 3/3 RNF cumplen; no se genera el informe.")
N_U4 = len(re.findall(r"test_u4_error_de_contenido_produce_rechazo_controlado\[", pruebas_txt))
N_ILEG = len(re.findall(r"test_u4_archivo_ilegible\[", pruebas_txt))
VERSION = re.search(r'__version__ = "([^"]+)"', leer("transmision/__init__.py")).group(1)
N_MUT = re.search(r"Contenidos mutados: (\d+)", rnf_txt).group(1)

# ------------------------------------------------------------ estilos
base = ParagraphStyle("base", fontName="DV", fontSize=8.5, leading=10.9, alignment=TA_LEFT, spaceAfter=3)
h1 = ParagraphStyle("h1", parent=base, fontName="DV-B", fontSize=10.8, leading=13, textColor=AZUL, spaceBefore=7,
                    spaceAfter=3)
h2 = ParagraphStyle("h2", parent=base, fontName="DV-B", fontSize=8.8, leading=11, spaceBefore=3, spaceAfter=2)
tit = ParagraphStyle("tit", parent=base, fontName="DV-B", fontSize=16, leading=19, textColor=AZUL, spaceAfter=2)
cel = ParagraphStyle("cel", parent=base, fontSize=7.3, leading=8.9, spaceAfter=0)
celb = ParagraphStyle("celb", parent=cel, fontName="DV-B")
pie = ParagraphStyle("pie", parent=base, fontSize=7, textColor=colors.grey)
bul = ParagraphStyle("bul", parent=base, leftIndent=9, bulletIndent=0, spaceAfter=1.5)


def P(t, s=base):
    return Paragraph(t, s)


def B(t):
    return Paragraph(t, bul, bulletText="•")


def tabla(filas, anchos, cabecera=True, fuente=cel):
    datos = [[Paragraph(str(c), celb if (cabecera and i == 0) else fuente) for c in fila] for i, fila in enumerate(filas)]
    t = Table(datos, colWidths=[a * cm for a in anchos], repeatRows=1 if cabecera else 0)
    est = [("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b8c0d0")), ("VALIGN", (0, 0), (-1, -1), "TOP"),
           ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
           ("TOPPADDING", (0, 0), (-1, -1), 1.8), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.8)]
    if cabecera:
        est.append(("BACKGROUND", (0, 0), (-1, 0), GRIS))
    t.setStyle(TableStyle(est))
    return t


def numerar(titulo):
    def dibujar(canvas, doc):
        canvas.saveState()
        canvas.setFont("DV", 7)
        canvas.setFillColor(colors.grey)
        canvas.drawString(1.8 * cm, 1.0 * cm, f"{titulo} · La última transmisión · motor v{VERSION}")
        canvas.drawRightString(letter[0] - 1.8 * cm, 1.0 * cm, f"Pág. {doc.page}")
        canvas.restoreState()
    return dibujar


# =============================================================== INFORME
def informe():
    s = []
    s += [P("La última transmisión — Informe del parcial", tit),
          P("Parcial práctico de Ingeniería de Software · motor de historias interactivas", base),
          tabla([["Integrantes", "Esteban Ramírez Rios - Emmanuel David Angulo"],
                 ["Versión descrita", f"Motor v{VERSION} (v1.0.0 es la versión previa; v1.1.0 incorpora la solicitud de cambio de la hora 6, ver §8). "
                  "Anexo: <b>anexo.pdf</b> (diagramas A, matriz de trazabilidad B, tablero C)."],
                 ["Entrega", f"14 de octubre de 2026 · Repositorio: historial en evidencia/historial_git.txt"]],
                [3.0, 14.8], cabecera=False)]

    # ---- 1
    s += [P("1. Fundamentos (Unidad 1)", h1),
          P("<b>Problema.</b> Un colectivo de escritores prepara una ficción interactiva para un festival universitario y "
            "no puede depender de un programador cada vez que cambia una escena o una decisión. Necesita un motor que "
            "cargue relatos desde archivos, ofrezca opciones condicionadas por lo ocurrido y avise qué corregir cuando "
            "un archivo es incorrecto. <b>Actores:</b> escritora principal (edita escenas), diseñador de la experiencia "
            "(define condiciones y efectos), coordinadora del festival (necesita diagnósticos, no cierres inesperados) y "
            "lector (juega). <b>Alcance:</b> motor local de consola, contenido en JSON, reglas de igualdad sobre "
            "booleanos, validación previa, tres finales y una segunda historia sin tocar el motor. <b>Fuera de alcance:</b> "
            "cuentas, base de datos, guardado, red, editor visual, audio, imágenes, lenguaje de expresiones, retroceso de varios niveles y rehacer."),
          tabla([["Riesgo", "Prob. / impacto", "Mitigación aplicada"],
                 ["R1. Contenido mal escrito produce un cierre del programa o una partida sin salida.", "Media / alta",
                  "Validación acumulativa antes de jugar (RF-12..17); bloqueo informado con opción de reiniciar (RF-09); "
                  f"pruebas de contenido mutado ({N_MUT} casos, RNF-03)."],
                 ["R2. El cambio de la hora 6 llega con poco tiempo y rompe la coherencia entre requisitos, modelos y código.",
                  "Alta / alta",
                  "Motor genérico sin lógica por historia (RNF-01); trazabilidad por ID (anexo B); tiempo reservado para "
                  "el cambio y pruebas de regresión; versiones y alcance de la evidencia identificados en evidencia/versiones.md."]],
                [6.2, 2.3, 9.3]),
          P("<b>Prioridad de atributos de calidad.</b> (1) <i>Modificabilidad del contenido</i>: es la razón de ser del "
            "producto, porque la escritora debe cambiar el relato sin tocar código. (2) <i>Confiabilidad</i>: un cierre "
            "inesperado arruina la experiencia en el festival. (3) <i>Claridad de los errores</i>: la coordinadora debe "
            "saber qué corregir. Quedan por debajo el rendimiento y la portabilidad (relatos pequeños, Python estándar).", base),
          P("<b>Responsabilidad profesional.</b> El relato es obra de sus autores: el motor no lo modifica ni lo copia, "
            "no recoge datos de los lectores (sin red ni guardado) y las historias de prueba se mantienen separadas del "
            "código. Se usan pocas dependencias, todas con licencia permisiva y declaradas (§7), y se declara el uso de "
            "herramientas de IA (§9) distinguiendo lo propio de lo adaptado.")]

    # ---- 2
    s += [P("2. Proceso (Unidad 2)", h1),
          P("<b>Elegido: incremental e iterativo</b> con incrementos cortos —(1) especificación y modelos, (2) núcleo del "
            "motor con pruebas, (3) verificación y entrega, (4) incremento del cambio—. <b>Alternativa comparada: cascada.</b> "
            "Se descartó porque concentra la validación al final y absorbe mal un cambio anunciado a mitad de la ventana; "
            "el enfoque incremental deja un producto ejecutable en cada paso y hace barato el cambio de la hora 6."),
          tabla([["Actividad", "Cómo se realiza en esta entrega"],
                 ["Especificación", "RF, RNF y criterios de aceptación escritos antes del código; supuestos registrados (§4)."],
                 ["Desarrollo", "Capas independientes (dominio, contenido, sesión, interfaz); motor incorporado en Git y revisiones posteriores."],
                 ["Validación", f"{N_PRUEBAS} pruebas automatizadas, tres recorridos de finales, 3 RNF medidos (§7)."],
                 ["Evolución", "Hora 6: análisis de impacto, cambio y trazabilidad actualizada; versiones y evidencia disponible documentadas (§8)."]],
                [3.0, 14.8])]

    # ---- 3
    s += [P("3. Agilidad (Unidad 3)", h1),
          P("<b>Backlog y tablero.</b> 24 ítems con responsable y estado en <i>evidencia/backlog.csv</i>; tablero Kanban "
            "(Por hacer / En curso / Hecho). Las capturas inicial y actual están en el anexo C; deben complementarse con la "
            "captura de la herramienta real del equipo. <b>Prácticas aplicadas:</b> (a) <i>criterios de aceptación "
            "ejecutables</i>: CA01–CA03 de la guía son pruebas automáticas, no solo texto; (b) <i>integración frecuente con "
            "pruebas antes de cada commit</i> y revisión cruzada entre integrantes. <b>Alternativa descartada:</b> programación "
            "en pareja síncrona, inviable en una ventana asincrónica; se sustituyó por revisión cruzada."),
          P("<b>Definición de terminado:</b> el ítem tiene código o documento en Git; las pruebas relacionadas pasan; el "
            "requisito tiene criterio de aceptación; el otro integrante lo revisó; la trazabilidad indica dónde está la evidencia."),
          P("<b>Aprendizaje y mejora.</b> La primera medición de RNF-01 buscó los identificadores de las historias "
            "como texto dentro del código y marcó «no cumple» por la palabra «entrada» en dos docstrings: un falso positivo "
            "del instrumento, no del motor. <i>Acción:</i> medir con análisis de sintaxis (<i>ast</i>) solo sobre literales y "
            "nombres ejecutables, y comprobar siempre el instrumento antes de interpretar su resultado.")]

    # ---- 4
    rf = [["ID", "N", "Requisito (comportamiento observable)", "Criterio de aceptación"],
          ["RF-01", "N01", "Cargar una historia desde un archivo JSON indicado por ruta.", "Cargar la_ultima_transmision.json da 6 escenas; cargar el_faro.json funciona sin editar código."],
          ["RF-02", "N01", "La historia define la escena inicial y los valores iniciales de las variables; toda partida nueva parte de ahí.", "Partida nueva: escena E1, conoce_origen y confia_en_la_voz en falso."],
          ["RF-03", "N02", "Mostrar el texto de la escena actual.", "Al iniciar se muestra el texto de E1."],
          ["RF-04", "N02", "Mostrar solo las opciones cuyas condiciones se cumplen (todas las igualdades; mapa vacío = visible).", "CA01: tras revisar e investigar, E3 muestra «Activar con código» y «Cortar»; sin investigar, «Activar sin verificar» y «Cortar»."],
          ["RF-05", "N03", "Al elegir una opción habilitada, aplicar sus efectos y pasar a su destino.", "Investigar en E2 deja conoce_origen en verdadero y lleva a E3."],
          ["RF-06", "N03", "Rechazar una opción inexistente, no habilitada o elegida en una escena final, con motivo y sin alterar escena, variables ni historial.", "CA02: «activar con código» sin conocer el origen se rechaza aunque se envíe su ID; sigue en E3."],
          ["RF-07", "N03", "Rechazar entradas de teclado no reconocidas sin alterar la partida.", "Escribir «abc» o «9» muestra «Entrada no válida» y la escena no cambia."],
          ["RF-08", "N04", "Recordar durante la partida el valor de cada variable y usarlo en las condiciones posteriores.", "El efecto de E2 habilita una opción distinta en E3."],
          ["RF-09", "N04", "Si una escena no final no tiene opciones habilitadas, informar el bloqueo y permitir reiniciar.", "Historia de prueba bloqueada: se muestra «[Bloqueo]» y se ofrece jugar de nuevo."],
          ["RF-10", "N05", "Reconocer una escena final, mostrar su texto y avisar el fin.", "Los tres recorridos terminan en E4, E5 y E6 con «FIN DE LA HISTORIA»."],
          ["RF-11", "N05", "Iniciar otra partida restaurando escena y variables iniciales y descartando el historial.", "Tras un final, reiniciar vuelve a E1 con variables iniciales; no queda estado previo."],
          ["RF-12", "N06", "Rechazar antes de jugar un archivo inexistente, ilegible, no UTF-8, no JSON o de estructura incorrecta.", "Un JSON truncado da E_ILEGIBLE con línea y columna."],
          ["RF-13", "N06", "Rechazar campos obligatorios ausentes (historia, escena, opción).", "Quitar «titulo» o el «destino» de una opción da E_CAMPO_AUSENTE con el campo."],
          ["RF-14", "N06", "Rechazar inicio inexistente, IDs de escena repetidos, IDs de opción repetidos en su escena y destinos inexistentes.", "CA03: destino E99 da E_DESTINO con ‘E99’ y no abre sesión."],
          ["RF-15", "N06", "Rechazar variables no declaradas y valores no booleanos en variables, condiciones y efectos.", "Efecto con valor 1 o variable «fantasma» da E_NO_BOOL / E_VARIABLE."],
          ["RF-16", "N06", "Rechazar escenas finales con opciones y no finales sin ellas.", "Escena final con una opción o no final vacía da E_FINAL_OPCIONES."],
          ["RF-17", "N06", "Informar cada rechazo con causa y campo/ID, acumulando todos los problemas, sin abrir sesión jugable.", "Un archivo con dos errores informa ambos en un solo mensaje."],
          ["RF-18", "N01, N06", "Permitir validar sin jugar (--validar) y reproducir un recorrido por IDs (--ruta).", "Códigos de salida 0, 1 y 2 según el caso."],
          ["RF-19", "N03, N04", "Cambio hora 6. Deshacer la última decisión restaura exactamente la escena, las variables y el historial anteriores a la última elección válida.", "Desde E2, investigar lleva a E3 con conoce_origen verdadero; deshacer devuelve a E2 con conoce_origen falso."],
          ["RF-20", "N03, N04", "Cambio hora 6. El retroceso es de un solo nivel: tras deshacer no hay otro hasta una nueva elección válida; al comenzar y tras reiniciar no hay retroceso disponible. No se exige rehacer.", "Un segundo deshacer no cambia nada y se informa; al continuar sin investigar, E3 muestra «Activar sin verificar» y «Cortar»."],
          ["RF-21", "N03", "Cambio hora 6. Una opción inexistente o no habilitada no modifica la sesión ni sustituye la última elección válida que se deshará.", "Tras una entrada inválida, deshacer revierte la elección válida anterior."],
          ["RF-22", "N03, N05", "Cambio hora 6. Se puede deshacer desde un final: se vuelve a la escena desde la que se eligió y se restauran los valores previos.", "Desde E4, E5 o E6, deshacer regresa a E3 con las variables previas a esa elección."]]
    rnf = [["ID", "Atributo", "Requisito medible", "Procedimiento (reproducible)", "Resultado"],
           ["RNF-01", "Modificabilidad", "Incorporar una historia nueva de ≥ 3 escenas sin modificar ningún archivo del motor; 0 identificadores de historia en su código.",
            "pruebas/verificar_rnf.py: hash SHA-256 de transmision/*.py antes y después de cargar y jugar el_faro.json; análisis ast de literales y nombres.",
            "0 archivos modificados; 0 apariciones; 4 escenas, final alcanzado."],
           ["RNF-02", "Claridad de errores", "10 de 10 variantes de error informan causa (código) y campo o ID involucrado.",
            "Mismo script: genera una variante por categoría desde el JSON real y comprueba el mensaje.", "10/10."],
           ["RNF-03", "Confiabilidad", "0 excepciones no controladas ante contenido o entradas inválidas.",
            f"Mismo script, semilla 20261014: {N_MUT} contenidos mutados y 500 partidas con entradas aleatorias al motor y a la consola.", "0 excepciones."]]
    s += [P("4. Requerimientos (Unidad 4)", h1),
          P("Los RF son atómicos y se vinculan con las necesidades N01–N06 de la guía; cada uno se traza a modelos, componentes y evidencia en el anexo B.", base),
          tabla(rf, [1.1, 1.1, 7.6, 8.0]),
          Spacer(1, 4),
          P("Requisitos no funcionales medibles", h2),
          tabla(rnf, [1.2, 2.0, 4.8, 6.4, 3.4]),
          Spacer(1, 3),
          P("Conflicto del cliente y acuerdo provisional", h2),
          P("La escritora quiere poder retroceder siempre; el diseñador quiere decisiones irreversibles. <b>Pregunta de "
            "aclaración:</b> ¿el retroceso debe existir siempre, solo en escenas que el relato marque como reversibles, o "
            "nunca? <b>Acuerdo provisional (v1.0.0):</b> no implementar retroceso, sin presuponer la decisión del cliente. "
            "<b>Reemplazado en la hora 6:</b> el cliente decidió permitir deshacer solo la última decisión (RF-19 a RF-22); "
            "la pregunta de «siempre / solo en escenas reversibles / nunca» queda resuelta como «un nivel, en cualquier escena»."),
          P("Preguntas y supuestos", h2),
          B("<b>P1.</b> ¿Son obligatorios «condiciones» y «efectos» aunque estén vacíos? <i>Supuesto:</i> sí, el contrato los lista como campos de la opción; si faltan se informa E_CAMPO_AUSENTE."),
          B("<b>P2.</b> ¿El lector elige por número o por ID? <i>Supuesto:</i> ve opciones numeradas; el motor acepta también el ID y rechaza el de una opción no habilitada (CA02)."),
          B("<b>P3.</b> ¿Se muestran las variables al lector? <i>Supuesto:</i> no; el estado es interno y solo se ve por sus consecuencias."),
          B("<b>P4.</b> ¿Debe detectarse un final inalcanzable o un ciclo? <i>Respuesta de la guía:</i> no se exige; solo se informa el bloqueo durante la partida."),
          P("Defecto detectado en la revisión y su corrección", h2),
          P("Revisor: Emmanuel David Angulo. El borrador de RF-04 decía «en E3 deben verse exactamente dos opciones»: ataba el requisito a una escena de "
            "la historia y contradecía la exigencia de que el motor no tenga decisiones específicas de E1, E2 u otros IDs. "
            "<b>Corrección:</b> RF-04 se redactó como regla general (mostrar solo opciones habilitadas) y el caso de E3 pasó a ser su criterio "
            "de aceptación CA01.")]

    # ---- 5
    s += [P("5. Modelado (Unidad 5)", h1),
          tabla([["Modelo", "Figura", "Qué representa"],
                 ["Contexto", "A.1", "Escritora, diseñador, coordinadora y lector alrededor del motor y los archivos JSON."],
                 ["Casos de uso", "A.2", "CU1 cargar, CU2 validar, CU3 ver escena, CU4 elegir, CU5 reiniciar, CU6 reproducir recorrido."],
                 ["Clases del dominio", "A.3", "Historia, Escena, Opción, Sesión, Diagnóstico y las dos excepciones del motor."],
                 ["Secuencia: elegir una opción", "A.4", "Consola, Sesión, reglas e Historia, con la rama de opción no habilitada (estado intacto)."],
                 ["Estados de una sesión", "A.5", "EnCurso, Bloqueada y Finalizada; reiniciar vuelve a EnCurso."]],
                [4.2, 1.4, 12.2]),
          P("Los modelos usan el mismo vocabulario que los requisitos y el código (historia, escena, opción, condición, efecto, "
            "variable, sesión, diagnóstico). El mapa narrativo (A.7) ayuda a leer la historia, pero no sustituye estos modelos.", base)]

    # ---- 6
    s += [P("6. Arquitectura (Unidad 6)", h1),
          P("Arquitectura en capas con dependencias en un solo sentido (anexo A.6): la <b>interfaz</b> (consola) usa la "
            "<b>sesión</b> y el <b>cargador</b>; la sesión usa las <b>reglas</b> y el <b>modelo</b>; el <b>contenido</b> (cargador, "
            "validador, diagnóstico) produce el modelo a partir de los archivos. El dominio no conoce ni la consola ni el disco."),
          tabla([["Componente", "Responsabilidad"],
                 ["consola", "Entrada y salida, menús, reinicio, códigos de salida. Sin reglas del juego."],
                 ["sesion", "Escena actual, variables, historial; elegir, reiniciar, detectar bloqueo; no modifica la historia."],
                 ["reglas / modelos", "Evaluar condiciones, aplicar efectos (funciones puras); estructuras inmutables de la historia."],
                 ["cargador / validador / diagnostico", "Leer el archivo, validar todos los casos de la guía y construir el modelo o informar diagnósticos."],
                 ["historias/*.json", "Datos de los escritores; se editan sin tocar código."]],
                [4.6, 13.2]),
          P("Decisión D1 — contenido declarativo en JSON, validado antes de jugar", h2),
          P("<b>Contexto:</b> la escritora no programa y el diseñador necesita condiciones sobre lo ocurrido. <b>Alternativas:</b> "
            "(a) historias escritas como código Python, (b) YAML, (c) reglas fijas en el motor. <b>Elección:</b> JSON, que la guía "
            "propone y la biblioteca estándar lee. <b>Consecuencias:</b> +modificabilidad y validación centralizada; −JSON no admite "
            "comentarios y es sensible a comas, lo que se compensa con errores de sintaxis con línea y columna (RF-12)."),
          P("Decisión D2 — estado de la partida separado de un modelo inmutable", h2),
          P("<b>Contexto:</b> reiniciar debe borrar todo rastro y un error no debe dejar la partida a medias. <b>Alternativas:</b> "
            "(a) mutar la historia durante el juego, (b) estado global, (c) registro de eventos. <b>Elección:</b> Historia inmutable; "
            "Sesión copia las variables, calcula los efectos sobre una copia y confirma el cambio al final. <b>Consecuencias:</b> reinicio "
            "trivial y elecciones atómicas (U3, U5); a cambio hay copias pequeñas de un diccionario, sin costo apreciable."),
          P("<b>Separación contenido–reglas–interfaz demostrada:</b> la segunda historia (el_faro.json, 4 escenas, variables y IDs "
            "distintos) se carga y se juega con el mismo código; RNF-01 confirma 0 archivos del motor modificados y 0 identificadores "
            "de historia en su código.")]

    # ---- 7
    s += [P("7. Implementación y verificación (Unidad 7)", h1),
          P("<b>Decisión de diseño detallado.</b> Las reglas son funciones puras en un módulo propio (<i>reglas.py</i>), y la consola "
            "recibe <i>leer</i> y <i>escribir</i> como parámetros. Así la lógica se prueba sin teclado ni pantalla, el acoplamiento "
            "entre interfaz y dominio es mínimo y cualquier otra interfaz (web, escritorio) podría reutilizar sesión y reglas."),
          tabla([["Biblioteca", "Uso", "Licencia"],
                 ["Biblioteca estándar de Python (json, argparse, dataclasses)", "Motor, validación y consola", "PSF License"],
                 ["pytest", "Pruebas automatizadas", "MIT"],
                 ["reportlab, matplotlib, graphviz (solo documentación, no son del producto)", "Generar informe, anexo y diagramas", "BSD, matplotlib License (BSD-style), EPL"]],
                [8.0, 6.0, 3.8]),
          Spacer(1, 3),
          KeepTogether(tabla([["Caso", "Qué comprueba", "Dónde"],
                 ["U1", "Condiciones cumplidas y no cumplidas habilitan solo las opciones correspondientes.", "pruebas/test_u1_condiciones.py"],
                 ["U2", "Elegir aplica efectos y avanza al destino correcto.", "pruebas/test_sesion.py"],
                 ["U3", "Opción inexistente o no habilitada deja el estado intacto.", "pruebas/test_sesion.py"],
                 ["U4", f"Errores de contenido: {N_U4} mutaciones del JSON real, {N_ILEG} archivos ilegibles, codificación, acumulación, CA03.", "pruebas/test_u4_validacion.py"],
                 ["U5", "Reiniciar restaura escena y variables iniciales y elimina el historial de retroceso (extendida en v1.1.0).", "pruebas/test_sesion.py"],
                 ["U6", "Deshacer restaura escena y variables, consume el retroceso; entrada inválida conserva el historial; nueva elección lo rehabilita; desde un final vuelve a E3.", "pruebas/test_u6_deshacer.py"],
                 ["I1", "Archivo real + motor + consola hasta los tres finales; segunda historia; CA01–CA03; deshacer desde un final (v1.1.0).", "pruebas/test_i1_integracion.py"],
                 ["RNF", "Versión reducida de los tres RNF.", "pruebas/test_rnf.py"]],
                [1.2, 11.0, 5.6])),
          P(f"<b>Resultados reales:</b> {N_PRUEBAS} pruebas pasan, ninguna falla (resultados/pruebas.txt); RNF-01, RNF-02 y RNF-03 cumplen "
            "(resultados/rnf.txt). <b>Fallos pendientes:</b> ninguno conocido en la versión 1.1.0. <b>Limitaciones:</b> no se analizan "
            "todos los caminos del relato; el retroceso es de un solo nivel y no hay rehacer, como pide el cliente.", base)]

    # ---- 8
    s += [P("8. Gestión del cambio (hora 6)", h1),
          P("<b>Versión previa declarada:</b> motor v1.0.0 (sin retroceso; acuerdo provisional «no implementar retroceso»). "
            "El repositorio recuperado no conserva esa versión ejecutable ni permite verificar su recuento histórico de pruebas. "
            f"<b>Versión posterior verificada:</b> motor v{VERSION} ({N_PRUEBAS} pruebas, 3/3 RNF), incorporado en el commit 2fa3133 "
            "e identificado con la etiqueta v1.1.0. Historial real: evidencia/historial_git.txt. Alcance de la evidencia: "
            "evidencia/versiones.md. Procedimiento y análisis completos: docs/gestion_cambio.md.", base),
          P("<b>Solicitud.</b> El colectivo decidió que el lector pueda deshacer su última decisión, revirtiendo sus consecuencias: restauración exacta de escena y "
            "variables, un solo nivel (sin rehacer), sin retroceso al comenzar ni tras reiniciar, entrada inválida que no altera el historial y deshacer desde "
            "E4, E5 o E6 hacia E3. Reemplaza el acuerdo provisional de no implementar retroceso.", base),
          tabla([["Artefacto", "Impacto"],
                 ["Requisitos", "Nuevos RF-19 a RF-22 (N03–N05); RF-11 se mantiene y se verifica también para el historial de retroceso; acuerdo provisional reemplazado."],
                 ["Modelos", "Clases: Sesion.deshacer(), puede_deshacer y SinRetroceso (A.3). Estados: transición deshacer() (A.5). Secuencia: guarda el estado previo al elegir (A.4). Contexto, casos de uso y componentes sin cambio estructural."],
                 ["Código", "sesion.py (instantánea previa solo tras validar la elección; deshacer la restaura y consume), consola.py (comando «u» y «@deshacer» en --ruta), __init__.py (versión 1.1.0). Reglas, validador, cargador, modelos e historias sin cambios."],
                 ["Pruebas", "Nueva U6 (pruebas/test_u6_deshacer.py); U5 extendida (reiniciar elimina el historial); I1 extendida (deshacer desde un final tras cargar el archivo y por consola). Mínimo final: 6 unitarios + 1 de integración."],
                 ["Backlog y trazabilidad", "B21–B23 en «Hecho»; matriz B del anexo con RF-19 a RF-22 y U6."]],
                [3.4, 14.4]),
          P(f"<b>Qué lo demuestra:</b> pruebas/test_u6_deshacer.py, test_sesion.py::test_u5_reiniciar_elimina_el_historial…, test_i1_integracion.py::test_i1_deshacer_desde_un_final…; "
            f"{N_PRUEBAS} pruebas pasan (resultados/pruebas.txt); RNF-01 sigue cumpliendo (el motor no incorpora IDs de la historia); demostración: "
            "<i>python -m transmision --ruta revisar,investigar,@deshacer,continuar</i>.", base)]

    # ---- 9
    s += [P("9. Fuentes, herramientas de apoyo y aportes", h1),
          P("<b>Herramientas de IA.</b> Se utilizó Claude (Anthropic) para generar un borrador del código, las pruebas, los diagramas y "
            "este informe a partir de la guía del parcial. Codex (OpenAI) se utilizó como apoyo para revisar la entrega, "
            "preparar el guion de demostración y ajustar este informe. <b>Verificación:</b> se ejecutaron las pruebas "
            f"automatizadas ({N_PRUEBAS} aprobadas; resultados/pruebas.txt) y la verificación de los requisitos no funcionales "
            "(3/3 cumplen; resultados/rnf.txt); se revisaron los diagramas y se corrigieron errores hallados, como un falso "
            "positivo de medición de RNF-01 y rombos de composición invertidos. <b>Revisión de los integrantes:</b> ambos "
            "integrantes revisamos el código, las pruebas y la documentación generados con asistencia de IA, comprobamos "
            "los resultados y comprendemos el funcionamiento de la solución. No se reutilizaron fragmentos de tutoriales."),
          P("<b>Aportes por integrante.</b> Esteban Ramírez Rios: análisis, requisitos, diagramas, implementación del motor, pruebas, "
            "verificación de RNF, documentación y evidencia (todas las tareas B01–B18 del tablero; ver historial_git.txt)."),
          P("Emmanuel David Angulo: revisión de requisitos (RF-04 y su corrección, §4), verificación, validación y asistencia "
            "en la ejecución de las pruebas.")]

    doc = SimpleDocTemplate(str(RAIZ / "docs" / "informe.pdf"), pagesize=letter, leftMargin=1.8 * cm, rightMargin=1.8 * cm,
                            topMargin=1.5 * cm, bottomMargin=1.6 * cm, title="La última transmisión — Informe",
                            author="Esteban Ramírez Rios y Emmanuel David Angulo")
    doc.build(s, onFirstPage=numerar("Informe"), onLaterPages=numerar("Informe"))


# =============================================================== ANEXO
def img(nombre, ancho_cm, alto_max_cm):
    from PIL import Image as PIL
    w, h = PIL.open(DIAG / nombre).size
    ancho = ancho_cm * cm
    alto = ancho * h / w
    if alto > alto_max_cm * cm:
        alto = alto_max_cm * cm
        ancho = alto * w / h
    return Image(str(DIAG / nombre), width=ancho, height=alto)


def anexo():
    s = [P("Anexo — La última transmisión", tit),
         P(f"Diagramas (A), matriz de trazabilidad (B) y tablero (C) · motor v{VERSION}. Referenciado desde el informe; no repite su contenido.", base),
         P("A. Diagramas", h1),
         P("A.1 Contexto", h2), img("01_contexto.png", 16.5, 6.2),
         P("A.2 Casos de uso", h2), img("02_casos_uso.png", 16.5, 8.5), PageBreak(),
         P("A.3 Clases del dominio", h2), img("03_clases.png", 17.4, 11.5),
         P("A.4 Secuencia: elegir una opción", h2), img("04_secuencia_elegir.png", 17.4, 11.2), PageBreak(),
         P("A.5 Estados de una sesión", h2), img("05_estados_sesion.png", 17.4, 6.5),
         P("A.6 Componentes y capas", h2), img("06_componentes.png", 14.0, 9.5),
         P("A.7 Mapa narrativo (apoyo; no es un modelo del software)", h2), img("07_mapa_narrativo.png", 17.4, 5.0), PageBreak()]

    s += [P("B. Matriz de trazabilidad", h1),
          P("Cada requisito se localiza en un modelo, un componente (archivo) y una evidencia ejecutable. "
            "Rutas relativas a la raíz del proyecto; «pruebas/» contiene las pruebas.", base)]
    M = [["Requisito", "N", "Modelo", "Componente", "Evidencia"],
         ["RF-01", "N01", "A.2 CU1; A.3", "transmision/cargador.py; validador.construir_historia", "test_i1_integracion.py::test_i1_los_tres_finales…, ::test_i1_segunda_historia…"],
         ["RF-02", "N01", "A.5 (inicio)", "modelos.Historia; sesion.Sesion.reiniciar", "test_sesion.py::test_u5_reiniciar_restaura…; test_i1…::ca01"],
         ["RF-03", "N02", "A.2 CU3", "consola.mostrar_escena", "test_i1_integracion.py::test_i1_consola_ruta_reproducida…"],
         ["RF-04", "N02", "A.2 CU3; A.4", "reglas.opcion_habilitada; Sesion.opciones_disponibles", "test_u1_condiciones.py (todo); test_i1…::ca01"],
         ["RF-05", "N03", "A.2 CU4; A.4; A.5", "Sesion.elegir; reglas.aplicar_efectos", "test_sesion.py::test_u2_*"],
         ["RF-06", "N03", "A.4 (alt); A.5", "Sesion.elegir; OpcionNoDisponible", "test_sesion.py::test_u3_*; test_i1…::ca02"],
         ["RF-07", "N03", "A.2 CU4", "consola._resolver, consola.jugar", "test_i1…::consola_interactiva_entrada_invalida…; RNF-03"],
         ["RF-08", "N04", "A.3 (Sesion.variables)", "Sesion (copia de variables); reglas", "test_sesion.py::test_u5_efectos_no_contaminan…; test_i1…::ca01"],
         ["RF-09", "N04", "A.5 (Bloqueada)", "Sesion.bloqueada; consola.mostrar_escena", "test_sesion.py::test_bloqueo_se_detecta…"],
         ["RF-10", "N05", "A.5 (Finalizada)", "Escena.final; Sesion.es_final", "test_i1…::test_i1_los_tres_finales…; test_sesion.py::test_escena_final…"],
         ["RF-11", "N05", "A.2 CU5; A.5", "Sesion.reiniciar; consola.jugar", "test_sesion.py::test_u5_*"],
         ["RF-12", "N06", "A.2 CU2", "cargador.cargar_archivo / cargar_desde_texto", "test_u4_validacion.py::test_u4_archivo_ilegible, ::…inexistente_y_codificacion"],
         ["RF-13", "N06", "A.2 CU2", "validador._revisar_campos", "test_u4_validacion.py (casos falta_*)"],
         ["RF-14", "N06", "A.2 CU2", "validador.validar", "test_u4_validacion.py (inicio, duplicados, destino); test_i1…::ca03"],
         ["RF-15", "N06", "A.2 CU2", "validador._validar_mapa", "test_u4_validacion.py (variable_no_declarada, no_booleana)"],
         ["RF-16", "N06", "A.2 CU2", "validador._validar_escena", "test_u4_validacion.py (final_con_opciones, no_final_sin_opciones)"],
         ["RF-17", "N06", "A.3 (Diagnostico, HistoriaInvalida)", "diagnostico.py; cargador.HistoriaInvalida", "test_u4_validacion.py::test_u4_acumula_varios_errores; resultados/rnf.txt (RNF-02)"],
         ["RF-18", "N01, N06", "A.2 CU6", "consola.main, consola.ejecutar_ruta", "test_i1…::test_i1_main_codigos_de_salida"],
         ["RF-19", "N03, N04", "A.3 (Sesion.deshacer); A.4; A.5", "sesion.Sesion.elegir (instantánea), Sesion.deshacer", "test_u6_deshacer.py::test_u6_deshacer_restaura…, ::test_u6_ejemplo_del_anexo…; test_i1…::test_i1_deshacer_desde_un_final…"],
         ["RF-20", "N03, N04", "A.5 (deshacer)", "Sesion.puede_deshacer; SinRetroceso; consola (u, @deshacer)", "test_u6…::test_u6_al_comenzar…, ::test_u6_una_nueva_eleccion…; test_sesion.py::test_u5_reiniciar_elimina…; test_i1…::test_i1_consola_deshacer…"],
         ["RF-21", "N03", "A.4 (alt); A.5", "Sesion.elegir (guarda la instantánea solo si la elección es válida)", "test_u6_deshacer.py::test_u6_entrada_invalida_conserva…"],
         ["RF-22", "N03, N05", "A.5 (Finalizada → EnCurso)", "Sesion.deshacer", "test_u6…::test_u6_se_puede_deshacer_desde_un_final…; test_i1…::test_i1_deshacer_desde_un_final…"],
         ["RNF-01", "—", "A.3; A.6", "Todo transmision/; historias/el_faro.json", "pruebas/verificar_rnf.py::rnf01; test_rnf.py; resultados/rnf.txt"],
         ["RNF-02", "—", "A.3", "diagnostico.py; validador.py", "pruebas/verificar_rnf.py::rnf02; test_u4_validacion.py; resultados/rnf.txt"],
         ["RNF-03", "—", "A.5", "cargador.py; sesion.py; consola.py", "pruebas/verificar_rnf.py::rnf03; test_rnf.py; resultados/rnf.txt"]]
    s += [tabla(M, [1.8, 1.1, 3.0, 5.0, 6.9]),
          P("RF-19 a RF-22 corresponden a la solicitud de cambio de la hora 6 (v1.1.0; ver docs/gestion_cambio.md).", pie),
          PageBreak(),
          P("C. Tablero", h1),
          P("Vistas generadas desde <i>evidencia/backlog.csv</i> con docs/generar_diagramas.py. Son una representación del backlog, "
            "no una captura de pantalla: deben acompañarse de las capturas inicial y final de la herramienta real del equipo.", base),
          img("08_tablero_inicial.png", 17.0, 19.5), PageBreak(),
          img("09_tablero_actual.png", 17.0, 19.5)]

    doc = SimpleDocTemplate(str(RAIZ / "docs" / "anexo.pdf"), pagesize=letter, leftMargin=1.8 * cm, rightMargin=1.8 * cm,
                            topMargin=1.5 * cm, bottomMargin=1.6 * cm, title="La última transmisión — Anexo",
                            author="Esteban Ramírez Rios y Emmanuel David Angulo")
    doc.build(s, onFirstPage=numerar("Anexo"), onLaterPages=numerar("Anexo"))


if __name__ == "__main__":
    informe()
    anexo()
    from pypdf import PdfReader
    for n in ("informe", "anexo"):
        print(n, len(PdfReader(str(RAIZ / "docs" / f"{n}.pdf")).pages), "páginas")
