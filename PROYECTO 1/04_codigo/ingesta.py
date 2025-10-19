# 04_codigo/ingesta.py
# Lectura, validación y estandarización de ESF/ER anonimizados.
# - Limpia filas vacías (sin codigo_mype o periodo).
# - Normaliza 'periodo' a formato YYYY-MM (acepta fechas variadas).
# - Valida identidad contable y utilidad.
# - Devuelve DataFrame listo para ratios + un reporte de calidad.

from __future__ import annotations
import re
from typing import Tuple, Dict
import pandas as pd

PERIODO_RE = re.compile(r"^\d{4}-\d{2}$")

class IngestaError(Exception):
    pass

def _validar_periodo(serie: pd.Series) -> pd.Series:
    return serie.fillna("").astype(str).str.match(PERIODO_RE)

def _normalizar_periodo(serie: pd.Series) -> pd.Series:
    s = serie.astype(str).str.strip()
    dt = pd.to_datetime(s, errors="coerce", format="%Y-%m")
    faltan = dt.isna()
    if faltan.any():
        dt2 = pd.to_datetime(s[faltan], errors="coerce", dayfirst=True, infer_datetime_format=True)
        dt.loc[faltan] = dt2
    out = s.copy()
    tiene_fecha = ~dt.isna()
    out.loc[tiene_fecha] = dt.loc[tiene_fecha].dt.strftime("%Y-%m")
    out = out.str.replace(r"^(\d{4})-(\d{1})$", r"\1-0\2", regex=True)
    return out

def _limpiar_vacias(df: pd.DataFrame) -> pd.DataFrame:
    """Elimina filas 'de relleno' sin codigo_mype o periodo (vacías/blancos/NaN)."""
    def _blank(x): 
        return x.isna() | (x.astype(str).str.strip().eq("")) | (x.astype(str).str.strip().str.lower().eq("nan"))
    m_codigo = _blank(df["codigo_mype"])
    m_periodo = _blank(df["periodo"])
    # Si falta cualquiera de las dos, se descarta (evita filas fantasma).
    keep = ~(m_codigo | m_periodo)
    return df.loc[keep].copy()

def leer_y_normalizar(xl_or_path) -> Tuple[pd.DataFrame, Dict]:
    # Abrir Excel
    xl = pd.ExcelFile(xl_or_path) if not isinstance(xl_or_path, pd.ExcelFile) else xl_or_path

    # Leer hojas
    try:
        esf = pd.read_excel(xl, "ESF")
    except Exception:
        raise IngestaError("No se encontró hoja 'ESF' en el Excel.")
    try:
        er = pd.read_excel(xl, "ER")
    except Exception:
        raise IngestaError("No se encontró hoja 'ER' en el Excel.")

    # Normalizar nombres
    esf.columns = [c.strip().lower() for c in esf.columns]
    er.columns  = [c.strip().lower() for c in er.columns]

    # Requisitos mínimos
    req_esf = {"codigo_mype","periodo","activo_corriente","activo_no_corriente",
               "pasivo_corriente","pasivo_no_corriente","patrimonio"}
    req_er  = {"codigo_mype","periodo","ingresos","costos","gastos"}
    faltan_esf = req_esf - set(esf.columns)
    faltan_er  = req_er  - set(er.columns)
    if faltan_esf: raise IngestaError(f"ESF: faltan columnas {faltan_esf}")
    if faltan_er:  raise IngestaError(f"ER: faltan columnas {faltan_er}")

    # --- LIMPIEZA DE FILAS VACÍAS (clave) ---
    esf["codigo_mype"] = esf["codigo_mype"].astype(str).str.strip()
    er["codigo_mype"]  = er["codigo_mype"].astype(str).str.strip()
    esf["periodo"] = esf["periodo"].astype(str).str.strip()
    er["periodo"]  = er["periodo"].astype(str).str.strip()

    esf = _limpiar_vacias(esf)
    er  = _limpiar_vacias(er)

    # Normalizar periodo a YYYY-MM
    esf["periodo"] = _normalizar_periodo(esf["periodo"])
    er["periodo"]  = _normalizar_periodo(er["periodo"])

    # Coerce numéricos
    for col in ["activo_corriente","activo_no_corriente","pasivo_corriente",
                "pasivo_no_corriente","patrimonio","efectivo"]:
        if col in esf.columns:
            esf[col] = pd.to_numeric(esf[col], errors="coerce")
    for col in ["ingresos","costos","gastos","utilidad"]:
        if col in er.columns:
            er[col] = pd.to_numeric(er[col], errors="coerce")

    # Validar periodo (ya limpio/normalizado)
    esf["_periodo_ok"] = _validar_periodo(esf["periodo"])
    er["_periodo_ok"]  = _validar_periodo(er["periodo"])
    if not esf["_periodo_ok"].all() or not er["_periodo_ok"].all():
        malos_esf = esf.loc[~esf["_periodo_ok"], ["codigo_mype","periodo"]].head(5).to_dict(orient="records")
        malos_er  = er .loc[~er ["_periodo_ok"], ["codigo_mype","periodo"]].head(5).to_dict(orient="records")
        raise IngestaError(
            "Hay periodos con formato inválido (use YYYY-MM). "
            f"Ejemplos ESF: {malos_esf} | ER: {malos_er}"
        )

    # Cálculos básicos
    esf["activo_total"] = esf["activo_corriente"].fillna(0) + esf["activo_no_corriente"].fillna(0)
    esf["pasivo_total"] = esf["pasivo_corriente"].fillna(0) + esf["pasivo_no_corriente"].fillna(0)
    er["utilidad_calc"] = er["ingresos"].fillna(0) - er["costos"].fillna(0) - er["gastos"].fillna(0)

    # Validaciones contables
    tol = 0.01
    esf["balance_ok"] = (esf["activo_total"] - (esf["pasivo_total"] + esf["patrimonio"].fillna(0))).abs() <= tol
    utilidad_ref = er["utilidad"] if "utilidad" in er.columns else er["utilidad_calc"]
    er["utilidad_ok"] = (utilidad_ref.fillna(er["utilidad_calc"]) - er["utilidad_calc"]).abs() <= tol

    # Merge clave
    key = ["codigo_mype","periodo"]
    df = pd.merge(esf, er, on=key, how="outer", suffixes=("_esf","_er"))

    # Salida estandar
    out = pd.DataFrame({
        "codigo_mype": df["codigo_mype"],
        "periodo": df["periodo"],
        "activo_corriente": df["activo_corriente"],
        "activo_no_corriente": df["activo_no_corriente"],
        "activo_total": df["activo_total"],
        "pasivo_corriente": df["pasivo_corriente"],
        "pasivo_no_corriente": df["pasivo_no_corriente"],
        "pasivo_total": df["pasivo_total"],
        "patrimonio": df["patrimonio"],
        "efectivo": df.get("efectivo", pd.NA),
        "ingresos": df["ingresos"],
        "costos": df["costos"],
        "gastos": df["gastos"],
        "utilidad": df["utilidad"] if "utilidad" in df.columns else df["utilidad_calc"],
        "utilidad_calc": df["utilidad_calc"],
        "balance_ok": df["balance_ok"],
        "utilidad_ok": df["utilidad_ok"],
    }).sort_values(["codigo_mype","periodo"]).reset_index(drop=True)

    report = {
        "n_filas": int(len(out)),
        "balance_ok_%": round(100 * out["balance_ok"].mean(), 2) if len(out) else 0.0,
        "utilidad_ok_%": round(100 * out["utilidad_ok"].mean(), 2) if len(out) else 0.0,
        "periodos_unicos": sorted(out["periodo"].dropna().astype(str).unique().tolist()),
    }
    return out, report
