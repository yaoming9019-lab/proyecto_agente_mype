# 04_codigo/nlg_report.py
from __future__ import annotations
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, DefaultDict
from collections import defaultdict
from jinja2 import Template
import textwrap
import shutil
import tempfile
import subprocess
import os

# === CONFIG: logo opcional (PNG/JPG). Si no tienes logo, deja "" ===
LOGO_PATH = r"E:\UC\logo_uc.png"  # <- AJUSTA o deja "" si no usarás logo

# ======= Plantilla HTML con branding UC =======
TPL_HTML = Template("""
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Informe MYPE – {{ fecha }}</title>
<style>
  :root{
    --fg:#0f172a;
    --muted:#64748b;
    --bg:#f8fafc;
    --card:#ffffff;
    --ok:#16a34a;      /* green-600 */
    --warn:#f59e0b;    /* amber-500 */
    --risk:#dc2626;    /* red-600 */
    --na:#6b7280;      /* gray-500 */
    --border:#e5e7eb;  /* gray-200 */
    --accent:#0033A0;  /* Azul UC aprox */
  }
  *{ box-sizing:border-box; }
  body{
    margin:0; padding:32px;
    font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, "Apple Color Emoji","Segoe UI Emoji";
    color:var(--fg);
    background:linear-gradient(180deg,#f8fafc 0%,#eef2f7 100%);
  }
  header{
    padding:16px 20px; margin-bottom:16px;
    background:linear-gradient(135deg,#e6eeff, #dbeafe);
    border:1px solid var(--border); border-radius:16px;
  }
  .hwrap{ display:flex; align-items:center; gap:16px; }
  .logo{ width:150px; height:auto; border-radius:8px; }
  h1{ margin:0 0 6px 0; font-size:28px; letter-spacing:.3px; color:#0b1220; }
  .meta{ font-size:12px; color:var(--muted) }
  h2{ margin:24px 0 8px; font-size:18px; color:#111827;}
  .cards{ display:grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap:12px; margin-top:10px; }
  .card{
    background:var(--card);
    border:1px solid var(--border);
    border-radius:14px; padding:14px 14px 12px;
    box-shadow:0 1px 2px rgba(15,23,42,.06);
    transition: box-shadow .2s ease, transform .2s ease;
  }
  .card:hover{ box-shadow:0 6px 16px rgba(15,23,42,.08); transform: translateY(-2px); }
  .empresa{ font-weight:700; font-size:14px; }
  .pill{ display:inline-flex; align-items:center; gap:6px; padding:2px 8px; border-radius:999px; color:white; font-size:12px; font-weight:700 }
  .ok{ background:var(--ok); } .atencion{ background:var(--warn); } .riesgo{ background:var(--risk);} .na{ background:var(--na);}
  .titulo{ font-weight:600; }
  .mensaje{ margin-top:4px; color:#334155; font-size:13px; }
  table{ width:100%; border-collapse:separate; border-spacing:0; margin-top:6px; }
  th, td{ padding:10px 12px; text-align:left; border-bottom:1px solid var(--border); }
  thead th{
    background:#eef2ff;
    font-size:12px; color:#1f2a44; text-transform:uppercase; letter-spacing:.04em;
    border-top-left-radius:8px; border-top-right-radius:8px;
  }
  tbody tr:nth-child(even){ background:#fafbff; }
  tbody tr:hover{ background:#f3f6ff; }
  .section{
    background:var(--card); border:1px solid var(--border);
    border-radius:16px; padding:14px 16px; margin-top:16px;
  }
  .badge{ display:inline-block; padding:2px 8px; border-radius:999px; font-size:12px; color:#334155; background:#e2e8f0; }
  .kpi{ font-size:28px; font-weight:800; color:var(--accent) }
  .footer{ margin-top:18px; font-size:12px; color:var(--muted); }
</style>
</head>
<body>
<header>
  <div class="hwrap">
    {% if logo_src %}
      <img src="{{ logo_src }}" alt="UC" class="logo">
    {% endif %}
    <div>
      <h1>Informe de Interpretación – MYPE</h1>
      <div class="meta">Generado: {{ fecha }} &nbsp;|&nbsp; Periodos: {{ periodos if periodos else "—" }}</div>
    </div>
  </div>
</header>

<div class="section">
  <h2>Validaciones de calidad</h2>
  <div class="cards" style="grid-template-columns: repeat(auto-fill, minmax(260px,1fr));">
    <div class="card">
      <div class="titulo">Balance OK</div>
      <div class="kpi">{{ report.balance_ok_ }}%</div>
      <div class="mensaje">Porcentaje de filas que cumplen Activo = Pasivo + Patrimonio.</div>
    </div>
    <div class="card">
      <div class="titulo">Utilidad OK</div>
      <div class="kpi">{{ report.utilidad_ok_ }}%</div>
      <div class="mensaje">Porcentaje de filas con Utilidad = Ingresos − Costos − Gastos.</div>
    </div>
  </div>
</div>

<div class="section">
  <h2>Semáforo y hallazgos (último periodo por MYPE)</h2>
  {% if empresas|length == 0 %}
    <div class="mensaje">No se encontraron hallazgos. Cargue datos válidos para ver resultados.</div>
  {% endif %}

  {% for emp in empresas %}
    <div class="card">
      <div class="empresa">{{ emp.codigo_mype }} <span class="badge">Periodo {{ emp.periodo }}</span></div>
      <div class="cards">
      {% for h in emp.hallazgos %}
        <div class="card">
          <div>
            <span class="pill {{ 'ok' if h.nivel=='OK' else 'atencion' if h.nivel=='Atención' else 'riesgo' if h.nivel=='Riesgo' else 'na' }}">
              {{ h.nivel }}
            </span>
            <span class="titulo">{{ h.titulo }}</span>
          </div>
          <div class="mensaje">{{ h.mensaje }}</div>
        </div>
      {% endfor %}
      </div>
    </div>
  {% endfor %}
</div>

<div class="section">
  <h2>Umbrales aplicados</h2>
  <table>
    <thead><tr><th>Métrica</th><th>Umbral</th></tr></thead>
    <tbody>
      {% for k,v in umbrales.items() %}
      <tr><td>{{ k }}</td><td>{{ v }}</td></tr>
      {% endfor %}
    </tbody>
  </table>
</div>

<div class="footer">* Informe generado por el prototipo Baseline (Fase 1). </div>
</body>
</html>
""")

def _agrupar_por_mype(hallazgos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_emp: DefaultDict[str, List[Dict[str, Any]]] = defaultdict(list)
    last_period: Dict[str, str] = {}
    for h in hallazgos:
        cod = str(h.get("codigo_mype", "—"))
        by_emp[cod].append(h)
        last_period[cod] = h.get("periodo", "—")
    result = []
    for cod, items in by_emp.items():
        result.append({
            "codigo_mype": cod,
            "periodo": last_period.get(cod, "—"),
            "hallazgos": items
        })
    result.sort(key=lambda x: x["codigo_mype"])
    return result

def generar_html(resultados: Dict[str, Any], report: Dict[str, Any]) -> str:
    """Rellena la plantilla con resultados, report y logo opcional."""
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
    periodos = ", ".join(report.get("periodos_unicos", []))
    hallazgos = resultados.get("hallazgos", [])
    empresas = _agrupar_por_mype(hallazgos)

    # Resolver logo (ruta absoluta o relativo). Si no existe, no se muestra.
    logo_src = None
    try:
        if LOGO_PATH and Path(LOGO_PATH).exists():
            # wkhtmltopdf maneja bien rutas absolutas
            logo_src = LOGO_PATH
    except Exception:
        logo_src = None

    ctx = {
        "fecha": fecha,
        "periodos": periodos,
        "report": {"balance_ok_": report.get("balance_ok_%", 0.0),
                   "utilidad_ok_": report.get("utilidad_ok_%", 0.0)},
        "umbrales": resultados.get("umbrales", {}),
        "empresas": empresas,
        "logo_src": logo_src
    }
    return TPL_HTML.render(**ctx)

# ======= Exportar PDF (WeasyPrint -> pdfkit/wkhtmltopdf -> subprocess -> ReportLab) =======
def exportar_pdf(html_str: str, out_path: Path) -> Path:
    """
    Orden de motores:
      1) WeasyPrint (si está disponible) para PDF fiel al HTML.
      2) pdfkit + wkhtmltopdf (estable en Windows) con enable-local-file-access.
      3) Llamada directa a wkhtmltopdf por subprocess (también con enable-local-file-access).
      4) ReportLab como respaldo (resumen) para no dejar PDF en blanco.
    Además, imprime en consola el motor usado para diagnóstico.
    """
    out_path = Path(out_path)

    # 1) WeasyPrint
    try:
        from weasyprint import HTML
        HTML(string=html_str).write_pdf(str(out_path))
        print("[PDF] Motor usado: WeasyPrint")
        return out_path
    except Exception as e:
        print(f"[PDF] WeasyPrint no disponible o falló: {e}")

    # 2) pdfkit + wkhtmltopdf
    wkhtml_default = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
    wkhtml = shutil.which("wkhtmltopdf") or wkhtml_default
    try:
        import pdfkit
        config = pdfkit.configuration(wkhtmltopdf=wkhtml)
        options = {
            "encoding": "UTF-8",
            "quiet": "",
            "enable-local-file-access": ""  # permite cargar imágenes/recursos locales
        }
        pdfkit.from_string(
            html_str,
            str(out_path),
            configuration=config,
            options=options
        )
        print(f"[PDF] Motor usado: pdfkit + wkhtmltopdf ({wkhtml})")
        return out_path
    except Exception as e:
        print(f"[PDF] pdfkit/wkhtmltopdf falló: {e}")

    # 3) Subprocess directo a wkhtmltopdf (con archivo temporal)
    try:
        if not os.path.exists(wkhtml):
            raise FileNotFoundError(f"wkhtmltopdf no encontrado en {wkhtml}")

        # Guardar HTML a un temporal
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as tmp:
            tmp.write(html_str)
            html_tmp = tmp.name

        cmd = [
            wkhtml,
            "--encoding", "utf-8",
            "--enable-local-file-access",  # permite archivos locales
            html_tmp,
            str(out_path)
        ]
        subprocess.run(cmd, check=True)
        print(f"[PDF] Motor usado: subprocess wkhtmltopdf ({wkhtml})")

        try:
            os.remove(html_tmp)
        except Exception:
            pass

        return out_path
    except Exception as e:
        print(f"[PDF] Subprocess wkhtmltopdf falló: {e}")

    # 4) Fallback final: ReportLab (resumen)
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import cm

        c = canvas.Canvas(str(out_path), pagesize=A4)
        w, h = A4
        y = h - 2*cm

        def draw_line(text, font="Helvetica", size=10, dy=0.6*cm):
            nonlocal y
            c.setFont(font, size)
            import textwrap as _tw
            for line in _tw.wrap(text, width=95):
                if y < 2*cm:
                    c.showPage(); y = h - 2*cm
                    c.setFont(font, size)
                c.drawString(2*cm, y, line)
                y -= 0.45*cm
            y -= (dy - 0.45*cm)

        c.setFont("Helvetica-Bold", 16)
        c.drawString(2*cm, y, "Informe MYPE (resumen)")
        y -= 1.0*cm
        draw_line(datetime.now().strftime("Generado: %Y-%m-%d %H:%M"))
        draw_line("Este PDF es un resumen. Para visual completo, consulte el HTML estilizado.")
        c.showPage(); c.save()
        print("[PDF] Motor usado: ReportLab (resumen)")
        return out_path
    except Exception as e:
        print(f"[PDF] ReportLab también falló: {e}")
        Path(out_path).write_bytes(b"")
        return out_path

