"""Genera los diagramas y las vistas de tablero del anexo. Requiere graphviz (dot) y matplotlib.
Uso:  python docs/generar_diagramas.py      (se ejecuta desde la raíz del proyecto)"""
import csv
import pathlib
import subprocess

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

RAIZ = pathlib.Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "docs" / "diagramas"
SALIDA.mkdir(parents=True, exist_ok=True)

BASE = 'graph [fontname="DejaVu Sans", pad=0.2]; node [fontname="DejaVu Sans", fontsize=11]; edge [fontname="DejaVu Sans", fontsize=9];'


def dot(nombre: str, fuente: str) -> None:
    (SALIDA / f"{nombre}.dot").write_text(fuente, encoding="utf-8")
    subprocess.run(["dot", "-Tpng", "-Gdpi=170", str(SALIDA / f"{nombre}.dot"), "-o", str(SALIDA / f"{nombre}.png")],
                   check=True)


# ---------------------------------------------------------------- contexto
dot("01_contexto", f'''digraph G {{ rankdir=LR; {BASE}
 node [shape=box, style="rounded,filled", fillcolor="#eef3fb", color="#46618f"];
 esc [label="Escritora principal\\n(edita escenas)"];
 dis [label="Diseñador\\n(define condiciones y efectos)"];
 coo [label="Coordinadora del festival\\n(verifica el contenido)"];
 lec [label="Lector\\n(juega)"];
 arch [shape=note, fillcolor="#fff6dd", color="#a68a2b", label="Archivo de historia\\n(JSON)"];
 sis [shape=box3d, fillcolor="#dff1e2", color="#3b7a4b", label="Motor de historias\\ninteractivas"];
 esc -> arch [label="escribe"]; dis -> arch [label="define reglas"];
 arch -> sis [label="se carga"];
 coo -> sis [label="pide validar"]; sis -> coo [label="diagnósticos"];
 lec -> sis [label="elige opción"]; sis -> lec [label="escena y opciones"];
}}''')

# ---------------------------------------------------------------- casos de uso
dot("02_casos_uso", f'''digraph G {{ rankdir=LR; {BASE}
 node [shape=box, style="filled", fillcolor="#eef3fb", color="#46618f"];
 lec [label="«actor»\\nLector"]; coo [label="«actor»\\nCoordinadora / Escritora"];
 subgraph cluster_s {{ label="Motor de historias interactivas"; style="rounded"; color="#888888";
  node [shape=ellipse, fillcolor="#ffffff"];
  cu1 [label="CU1 Cargar historia"]; cu2 [label="CU2 Validar historia"];
  cu3 [label="CU3 Ver escena y opciones"]; cu4 [label="CU4 Elegir opción"];
  cu5 [label="CU5 Reiniciar partida"]; cu6 [label="CU6 Reproducir recorrido"];
 }}
 coo -> cu2; coo -> cu1; coo -> cu6; lec -> cu1; lec -> cu3; lec -> cu4; lec -> cu5;
 cu1 -> cu2 [style=dashed, label="«include»"];
 cu4 -> cu3 [style=dashed, label="«include»"];
 cu6 -> cu4 [style=dashed, label="«include»"];
}}''')

# ---------------------------------------------------------------- clases
dot("03_clases", f'''digraph G {{ rankdir=BT; {BASE}
 node [shape=record, fontsize=10, style=filled, fillcolor="#ffffff", color="#46618f"];
 Historia [label="{{Historia|titulo: str\\linicio: str\\lvariables: dict[str,bool]\\lescenas: dict[str,Escena]\\l|escena(id): Escena\\l}}"];
 Escena [label="{{Escena|id: str\\ltexto: str\\lfinal: bool\\lopciones: tuple[Opcion]\\l}}"];
 Opcion [label="{{Opcion|id: str\\ltexto: str\\ldestino: str\\lcondiciones: dict[str,bool]\\lefectos: dict[str,bool]\\l}}"];
 Sesion [label="{{Sesion|escena: Escena\\lvariables: dict\\lhistorial: list\\les_final: bool\\lbloqueada: bool\\lpuede_deshacer: bool\\l|opciones_disponibles()\\lelegir(opcion_id): Escena\\ldeshacer(): Escena\\lreiniciar()\\l}}", fillcolor="#dff1e2"];
 Reglas [label="{{«módulo» reglas|condiciones_cumplidas()\\lopcion_habilitada()\\laplicar_efectos()\\l}}"];
 Cargador [label="{{«módulo» cargador|cargar_archivo(ruta)\\lcargar_desde_texto(texto)\\l}}"];
 Validador [label="{{«módulo» validador|validar(datos): list[Diagnostico]\\lconstruir_historia(datos)\\l}}"];
 Diag [label="{{Diagnostico|codigo: str\\lmensaje: str\\lcampo: str\\l}}"];
 Inval [label="{{HistoriaInvalida «Exception»|diagnosticos: list\\lorigen: str\\l}}"];
 NoDisp [label="{{OpcionNoDisponible «Exception»}}"];
 SinRet [label="{{SinRetroceso «Exception»}}"];
 Consola [label="{{«módulo» consola|main()\\ljugar(sesion, leer, escribir)\\lejecutar_ruta()\\l}}", fillcolor="#fff6dd"];
 Escena -> Historia [arrowhead=diamond, label="1..*"];
 Opcion -> Escena [arrowhead=diamond, label="0..*"];
 Sesion -> Historia [label="recorre", arrowhead=vee];
 Sesion -> Reglas [style=dashed, arrowhead=vee, label="usa"];
 Sesion -> NoDisp [style=dashed, arrowhead=vee, label="lanza"];
 Sesion -> SinRet [style=dashed, arrowhead=vee, label="lanza"];
 Cargador -> Validador [style=dashed, arrowhead=vee, label="usa"];
 Cargador -> Inval [style=dashed, arrowhead=vee, label="lanza"];
 Inval -> Diag [arrowhead=vee, label="1..*"];
 Validador -> Diag [style=dashed, arrowhead=vee, label="produce"];
 Consola -> Sesion [arrowhead=vee, label="controla"];
 Consola -> Cargador [style=dashed, arrowhead=vee, label="usa"];
}}''')

# ---------------------------------------------------------------- estados
dot("05_estados_sesion", f'''digraph G {{ rankdir=LR; {BASE}
 ini [shape=circle, width=0.2, label="", style=filled, fillcolor="#222222"];
 node [shape=box, style="rounded,filled", fillcolor="#eef3fb", color="#46618f"];
 curso [label="EnCurso\\n(escena no final con opciones habilitadas)\\n――――――――――\\nelegir(válida) [destino no final con opciones] / aplicar efectos\\nelegir(inválida) / estado intacto\\ndeshacer() [hay elección previa] / restaurar escena y variables"];
 bloq [label="Bloqueada\\n(escena no final\\nsin opciones habilitadas)", fillcolor="#fde8e8", color="#aa3333"];
 fin [label="Finalizada\\n(escena final)", fillcolor="#dff1e2", color="#3b7a4b", peripheries=2];
 ini -> curso [label="nueva partida"];
 curso -> fin [label="elegir(opción válida)\\n[destino final]"];
 curso -> bloq [label="elegir(opción válida)\\n[destino sin opciones habilitadas]"];
 fin -> curso [label="deshacer()\\n[hay elección previa]"]; bloq -> curso [label="deshacer()\\n[hay elección previa]"];
 fin -> curso [label="reiniciar()"]; bloq -> curso [label="reiniciar()"];
}}''')

# ---------------------------------------------------------------- componentes
dot("06_componentes", f'''digraph G {{ rankdir=TB; compound=true; {BASE}
 node [shape=component, style=filled, fillcolor="#ffffff", color="#46618f"];
 subgraph cluster_ui {{ label="Interfaz"; style="rounded,filled"; fillcolor="#fff6dd"; color="#a68a2b"; consola [label="consola\\n(entrada/salida, menús)"]; }}
 subgraph cluster_app {{ label="Estado de la partida"; style="rounded,filled"; fillcolor="#dff1e2"; color="#3b7a4b"; sesion [label="sesion\\n(escena actual, variables,\\nhistorial, reinicio)"]; }}
 subgraph cluster_dom {{ label="Reglas y modelo"; style="rounded,filled"; fillcolor="#eef3fb"; color="#46618f";
   reglas [label="reglas\\n(condiciones y efectos)"]; modelos [label="modelos\\n(Historia, Escena, Opcion)"]; }}
 subgraph cluster_cont {{ label="Contenido"; style="rounded,filled"; fillcolor="#f3ecfb"; color="#6d4a99";
   cargador [label="cargador\\n(lee el archivo)"]; validador [label="validador\\n(10 códigos de error)"]; diagnostico [label="diagnostico"]; }}
 datos [shape=note, fillcolor="#fff6dd", color="#a68a2b", label="historias/*.json\\n(datos de los escritores)"];
 consola -> sesion; consola -> cargador;
 sesion -> reglas; sesion -> modelos; reglas -> modelos;
 cargador -> validador; validador -> diagnostico; cargador -> modelos; cargador -> datos [style=dashed, label="lee"];
}}''')

# ---------------------------------------------------------------- mapa narrativo
dot("07_mapa_narrativo", f'''digraph G {{ rankdir=LR; {BASE}
 node [shape=box, style="rounded,filled", fillcolor="#eef3fb", color="#46618f"];
 E4 [fillcolor="#dff1e2", peripheries=2, label="E4 Rescate"]; E5 [fillcolor="#fde8e8", peripheries=2, label="E5 El eco"];
 E6 [fillcolor="#eeeeee", peripheries=2, label="E6 Silencio"];
 E1 [label="E1 La señal"]; E2 [label="E2 El archivo"]; E3 [label="E3 La respuesta"];
 E1 -> E2 [label="revisar señal"];
 E2 -> E3 [label="investigar\\n[conoce_origen := true]"]; E2 -> E3 [label="continuar sin investigar"];
 E3 -> E4 [label="activar con código\\n{{conoce_origen = true}}\\n[confia := true]"];
 E3 -> E5 [label="activar sin verificar\\n{{conoce_origen = false}}\\n[confia := true]"];
 E3 -> E6 [label="cortar\\n[confia := false]"];
}}''')


# ---------------------------------------------------------------- secuencia (matplotlib)
def secuencia() -> None:
    nombres = ["Lector", "Consola", "Sesión", "reglas", "Historia"]
    xs = [1.0, 3.2, 5.6, 8.0, 10.2]
    fig, ax = plt.subplots(figsize=(11, 6.6))
    ax.set_xlim(0, 11.4)
    ax.set_ylim(-0.2, 12.4)
    ax.axis("off")
    for n, x in zip(nombres, xs):
        ax.add_patch(FancyBboxPatch((x - 0.7, 11.4), 1.4, 0.7, boxstyle="round,pad=0.02", fc="#eef3fb", ec="#46618f"))
        ax.text(x, 11.75, n, ha="center", va="center", fontsize=10, fontweight="bold")
        ax.plot([x, x], [0.2, 11.4], ls="--", color="#999999", lw=0.8)

    def msg(i, j, y, texto, ret=False, ls="-"):
        x1, x2 = xs[i], xs[j]
        ax.annotate("", xy=(x2, y), xytext=(x1, y),
                    arrowprops=dict(arrowstyle="->", color="#222222", lw=1.1, ls="--" if ret else ls))
        ax.text((x1 + x2) / 2, y + 0.14, texto, ha="center", va="bottom", fontsize=8.2)

    def auto(i, y, texto):
        x = xs[i]
        ax.annotate("", xy=(x, y - 0.35), xytext=(x, y), arrowprops=dict(arrowstyle="->", color="#222222",
                    connectionstyle="arc3,rad=-1.6", lw=1.0))
        ax.text(x + 0.45, y - 0.18, texto, fontsize=8.2, va="center")

    msg(0, 1, 10.7, "escribe «2»")
    msg(1, 2, 9.9, "opciones_disponibles()")
    msg(2, 3, 9.2, "opcion_habilitada(opción, variables) por cada opción")
    msg(2, 1, 8.5, "lista de opciones visibles", ret=True)
    msg(1, 2, 7.7, "elegir(id de la opción 2)")
    msg(2, 3, 7.0, "opcion_habilitada(opción, variables)")
    ax.add_patch(FancyBboxPatch((4.4, 1.95), 6.7, 4.4, boxstyle="square,pad=0", fc="none", ec="#aa3333", lw=1))
    ax.text(4.5, 6.1, "alt", fontsize=8.5, fontweight="bold", color="#aa3333")
    ax.text(4.95, 6.1, "[no existe o no está habilitada]", fontsize=8.2, color="#aa3333")
    msg(2, 1, 5.45, "OpcionNoDisponible (estado intacto)", ret=True)
    msg(1, 0, 4.8, "«Entrada no válida: …»", ret=True)
    ax.plot([4.4, 11.1], [4.3, 4.3], ls=":", color="#aa3333", lw=0.9)
    ax.text(4.5, 4.45, "[habilitada]", fontsize=8.2, color="#aa3333")
    msg(2, 3, 3.85, "aplicar_efectos(variables, efectos)")
    auto(2, 3.45, "guarda estado previo (RF-19);\nactualiza escena y variables")
    ax.text(9.2, 2.65, "", fontsize=8)
    msg(2, 4, 2.4, "escena(destino)")
    msg(2, 1, 1.55, "nueva Escena", ret=True)
    msg(1, 0, 0.85, "muestra texto y opciones", ret=True)
    fig.tight_layout()
    fig.savefig(SALIDA / "04_secuencia_elegir.png", dpi=170)
    plt.close(fig)


secuencia()


# ---------------------------------------------------------------- tableros (desde evidencia/backlog.csv)
def tablero(columna: str, archivo: str, titulo: str) -> None:
    with open(RAIZ / "evidencia" / "backlog.csv", encoding="utf-8") as fh:
        filas = list(csv.DictReader(fh))
    cols = ["Por hacer", "En curso", "Hecho"]
    colores = {"Por hacer": "#fde8e8", "En curso": "#fff6dd", "Hecho": "#dff1e2"}
    fig, ax = plt.subplots(figsize=(7.6, 9.8))
    ax.set_xlim(0, 3)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_title(titulo, fontsize=8.5, fontweight="bold")
    for c, nombre in enumerate(cols):
        items = [r for r in filas if r[columna] == nombre]
        ax.add_patch(FancyBboxPatch((c + 0.02, 0.01), 0.96, 0.93, boxstyle="round,pad=0.005", fc=colores[nombre],
                                    ec="#888888"))
        ax.text(c + 0.5, 0.955, f"{nombre} ({len(items)})", ha="center", fontsize=8.5, fontweight="bold")
        paso = min(0.0385, 0.9 / max(len(items), 1))
        for k, r in enumerate(items):
            y = 0.9 - k * paso
            ax.add_patch(FancyBboxPatch((c + 0.04, y - paso * 0.82), 0.92, paso * 0.78, boxstyle="round,pad=0.002",
                                        fc="white", ec="#bbbbbb", lw=0.6))
            titulo_corto = r["titulo"] if len(r["titulo"]) <= 33 else r["titulo"][:31] + "…"
            ax.text(c + 0.05, y - paso * 0.43, f"{r['id']} {titulo_corto}", fontsize=6.3, va="center")
            ax.text(c + 0.95, y - paso * 0.43, r["responsable"].replace("Esteban Ramírez Rios", "E. Ramírez"), fontsize=5.6,
                    va="center", ha="right", color="#555555")
    fig.tight_layout()
    fig.savefig(SALIDA / archivo, dpi=170)
    plt.close(fig)


tablero("estado_inicial", "08_tablero_inicial.png", "Tablero — captura inicial (vista generada desde evidencia/backlog.csv)")
tablero("estado_actual", "09_tablero_actual.png", "Tablero — estado actual (vista generada desde evidencia/backlog.csv)")
print("Diagramas generados en", SALIDA)
