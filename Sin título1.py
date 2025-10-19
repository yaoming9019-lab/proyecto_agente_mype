# ============================================================
# Diagrama de Arquitectura del Agente Inteligente
# Autor: José Antonio Rojas Guillén
# Universidad Continental - Proyecto de Innovación
# ============================================================

# Requiere: matplotlib
# Si no lo tienes instalado: pip install matplotlib

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib import patheffects as pe
import os

# ---------- Función para crear cajas ----------
def add_box(ax, xy, w, h, text, fc="#FFFFFF", ec="#222222",
            fontsize=11, bold=False):
    x, y = xy
    box = FancyBboxPatch((x, y), w, h,
                         boxstyle="round,pad=0.02,rounding_size=10",
                         linewidth=1.2, edgecolor=ec, facecolor=fc)
    ax.add_patch(box)
    t = ax.text(x + w/2, y + h/2, text, ha="center", va="center",
                fontsize=fontsize, fontweight=("bold" if bold else "normal"),
                color="#111111", wrap=True)
    # halo blanco para mejorar legibilidad
    t.set_path_effects([pe.withStroke(linewidth=3, foreground="white")])
    return box

# ---------- Función para crear flechas ----------
def add_arrow(ax, src_xy, dst_xy, connectionstyle="arc3,rad=0.0"):
    arrow = FancyArrowPatch(posA=src_xy, posB=dst_xy,
                            arrowstyle="-|>", mutation_scale=12,
                            linewidth=1.15, color="#333333",
                            connectionstyle=connectionstyle)
    ax.add_patch(arrow)

# ---------- Configuración del lienzo ----------
fig_w, fig_h = 11, 6.5
plt.figure(figsize=(fig_w, fig_h), dpi=200)
ax = plt.gca()
ax.set_xlim(0, 100)
ax.set_ylim(0, 60)
ax.axis("off")

# ---------- Coordenadas ----------
y_top, y_mid, y_low = 42, 24, 6
x0, x1, x2, x3, x4 = 4, 22, 40, 58, 76
w, h = 16, 12

# ---------- Colores por etapas ----------
c_in  = "#D8EBFF"  # Entrada
c_proc = "#EDE7FF" # Procesamiento
c_out = "#E5FFF1"  # Salida

# ---------- Cajas principales ----------
b_user = add_box(ax, (x0, y_top), w, h,
                 "Usuario / MYPE\n(Estados financieros)",
                 fc=c_in, bold=True)

b_ingesta = add_box(ax, (x1, y_top), w, h,
                    "Ingesta &\nNormalización\n• Carga PDF/Excel\n• Validaciones",
                    fc=c_in, fontsize=10)

b_dataset = add_box(ax, (x2, y_top), w, h,
                    "Dataset\nEstandarizado\n(ESF, ER)",
                    fc=c_proc, fontsize=10)

b_ratios = add_box(ax, (x2, y_mid), w, h,
                   "Ratios & Features\n• Liquidez, ROA, Margen\n• Endeudamiento",
                   fc=c_proc, fontsize=10)

b_reglas = add_box(ax, (x3, y_mid), w, h,
                   "Motor de Reglas\nContables\n(interpretación\nbaseline)",
                   fc=c_proc, fontsize=10)

b_analitica = add_box(ax, (x3, y_low), w, h,
                      "Analítica ligera\n(ARIMA / Regresión)",
                      fc=c_proc, fontsize=10)

b_xai = add_box(ax, (x4, y_mid), w, h,
                "Explicabilidad\nXAI (LIME/SHAP)\n¿Por qué?",
                fc=c_proc, fontsize=10, bold=True)

b_nlg = add_box(ax, (x4, y_top), w, h,
                "NLG → Informe /\nAlertas / Audio",
                fc=c_out, fontsize=10, bold=True)

b_panel = add_box(ax, (x1, y_low), w, h,
                  "Panel Web Mínimo\n(Streamlit)\n• Cargar archivos\n• Descargar informe",
                  fc=c_out, fontsize=10)

# ---------- Flechas de conexión ----------
add_arrow(ax, (x0 + w, y_top + h/2), (x1, y_top + h/2))   # User -> Ingesta
add_arrow(ax, (x1 + w, y_top + h/2), (x2, y_top + h/2))   # Ingesta -> Dataset
add_arrow(ax, (x2 + w/2, y_top), (x2 + w/2, y_mid + h))   # Dataset -> Ratios (down)
add_arrow(ax, (x2 + w, y_mid + h/2), (x3, y_mid + h/2))   # Ratios -> Reglas
add_arrow(ax, (x2 + w/2, y_mid), (x3 + w/2, y_low + h))   # Ratios -> Analítica (down)
add_arrow(ax, (x3 + w, y_mid + h/2), (x4, y_mid + h/2))   # Reglas -> XAI
add_arrow(ax, (x3 + w/2, y_low + h), (x4 + w/2, y_mid))   # Analítica -> XAI (up)
add_arrow(ax, (x4 + w/2, y_mid + h), (x4 + w/2, y_top))   # XAI -> NLG (up)
add_arrow(ax, (x1 + w/2, y_low + h), (x1 + w/2, y_top))   # Panel -> Ingesta (up)
add_arrow(ax, (x4, y_top + h/2), (x1 + w, y_low + h/2))   # NLG -> Panel (diagonal)

# ---------- Título ----------
ax.text(50, 57, "Arquitectura del Agente: Entrada → Procesamiento → Salida",
        ha="center", va="center", fontsize=14, fontweight="bold", color="#111111")

ax.text(50, 1.5,
        "Flujo: Usuario carga estados financieros → Normalización → Ratios → "
        "Reglas/Analítica → XAI → Informe/Alertas en el Panel",
        ha="center", va="bottom", fontsize=9, color="#333333")

# ---------- Guardar y mostrar ----------
png_path = "arquitectura_agente.png"
svg_path = "arquitectura_agente.svg"
plt.savefig(png_path, bbox_inches="tight", pad_inches=0.2)
plt.savefig(svg_path, bbox_inches="tight", pad_inches=0.2)
print("✅ Listo. Archivos generados:", png_path, "y", svg_path)

# (Opcional) abrir la imagen automáticamente
os.startfile(png_path)
