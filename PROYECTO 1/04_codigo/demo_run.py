# 04_codigo/demo_run.py
from pathlib import Path
import json

# --- Módulos del pipeline ---
from ingesta import leer_y_normalizar, IngestaError
from ratios_reglas import calcular_ratios_y_reglas
from nlg_report import generar_html, exportar_pdf


# ================== CONFIGURA AQUÍ ==================
# Excel de entrada (anonimizado) con hojas ESF y ER:
PATH_XLSX = Path(r"E:\UC\PROYECTO 1\02_data_anon\PLANTILLA_ESF_ER1.xlsx")

# Carpeta de salida para HTML/PDF y archivos auxiliares:
OUT_DIR = Path(r"E:\UC\PROYECTO 1\03_resultados")
# ====================================================


def main():
    # 0) Preparar carpeta de salida
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1) Comprobar que el Excel existe
    if not PATH_XLSX.exists():
        raise FileNotFoundError(f"No se encuentra el Excel: {PATH_XLSX}")

    # 2) Ingesta + validación
    try:
        df_estandar, report = leer_y_normalizar(str(PATH_XLSX))
    except IngestaError as e:
        print("❌ Ingesta/validación falló:")
        print(str(e))
        print("\nVerifica que tu Excel tenga las hojas ESF y ER con estas columnas mínimas:")
        print("- ESF: codigo_mype, periodo, activo_corriente, activo_no_corriente, pasivo_corriente, pasivo_no_corriente, patrimonio (opcional efectivo)")
        print("- ER : codigo_mype, periodo, ingresos, costos, gastos (opcional utilidad)")
        return
    except Exception as e:
        print("❌ Error inesperado en ingesta:", repr(e))
        return

    # 3) Cálculo de ratios + reglas
    try:
        resultados = calcular_ratios_y_reglas(df_estandar)
    except Exception as e:
        print("❌ Error calculando ratios/reglas:", repr(e))
        return

    # 4) Generar HTML y PDF
    try:
        html_str = generar_html(resultados, report)
        html_path = OUT_DIR / "informe.html"
        pdf_path  = OUT_DIR / "informe.pdf"

        html_path.write_text(html_str, encoding="utf-8")
        exportar_pdf(html_str, pdf_path)  # nlg_report elegirá el mejor motor disponible

        print("✔ Hecho. Revisa:")
        print(f" - HTML: {html_path}")
        print(f" - PDF : {pdf_path}")
    except Exception as e:
        print("❌ Error generando el informe:", repr(e))
        return

    # 5) Bloque de DIAGNÓSTICO y exportación (opcional, útil para auditoría)
    try:
        # A) Ver en consola el resumen de calidad (report)
        print("\n[DIAGNÓSTICO] Calidad de datos")
        print(" - Filas válidas:", report.get("n_filas"))
        print(" - Balance OK %:", report.get("balance_ok_%"))
        print(" - Utilidad OK %:", report.get("utilidad_ok_%"))
        periodos = ", ".join(report.get("periodos_unicos", [])) or "—"
        print(" - Periodos:", periodos)

        # B) Guardar report como JSON
        (OUT_DIR / "report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        # C) Exportar ratios a Excel/CSV
        df_rat = resultados.get("df_ratios")
        if df_rat is not None:
            try:
                df_rat.to_excel(OUT_DIR / "ratios.xlsx", index=False)
            except Exception:
                # Si no hay motor Excel, al menos CSV
                pass
            df_rat.to_csv(OUT_DIR / "ratios.csv", index=False, encoding="utf-8-sig")
            print(f" - Ratios exportados: {OUT_DIR / 'ratios.xlsx'} / {OUT_DIR / 'ratios.csv'}")

        # D) Resumen de niveles por empresa (si hay hallazgos)
        try:
            import pandas as pd
            df_h = pd.DataFrame(resultados.get("hallazgos", []))
            if not df_h.empty:
                pivot = (df_h
                         .pivot_table(index="codigo_mype", columns="nivel", values="titulo",
                                      aggfunc="count", fill_value=0)
                         .reset_index())
                pivot.to_excel(OUT_DIR / "resumen_niveles.xlsx", index=False)
                print(" - Resumen de niveles exportado:", OUT_DIR / "resumen_niveles.xlsx")
        except Exception as e:
            print(" - Aviso: no se pudo generar resumen_niveles.xlsx:", e)

    except Exception as e:
        print("⚠️  Bloque de diagnóstico falló (no crítico):", repr(e))


if __name__ == "__main__":
    main()
