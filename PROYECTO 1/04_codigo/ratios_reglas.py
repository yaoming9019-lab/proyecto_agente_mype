# 04_codigo/ratios_reglas.py
import math
import pandas as pd
from typing import Dict, Any, List

# Umbrales auditables (ajusta a tu criterio/validación de expertos)
UMBRALES = {
    "liquidez_ok": 1.2,                 # antes 1.0 (más estricto)
    "prueba_acida_ok": 1.0,             # antes 0.8
    "endeudamiento_alto": 0.6,          # antes 0.7 (más exigente)
    "margen_neto_bajo": 0.08,           # antes 0.05
    "roa_bajo": 0.03,                   # antes 0.02
    "efectivo_min_sobre_activo_corr": 0.12  # antes 0.10
}

def _safe_div(a, b):
    try:
        return float(a) / float(b) if b not in (0, None, 0.0) and not math.isnan(b) else float("nan")
    except Exception:
        return float("nan")

def calcular_ratios(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["liquidez"] = out.apply(lambda r: _safe_div(r["activo_corriente"], r["pasivo_corriente"]), axis=1)
    # Sin inventarios, prueba ácida ≈ liquidez; si tuvieras inventarios, descuéntalos
    out["prueba_acida"] = out["liquidez"]
    out["endeudamiento"] = out.apply(lambda r: _safe_div(r["pasivo_total"], r["activo_total"]), axis=1)
    out["margen_neto"] = out.apply(lambda r: _safe_div(r["utilidad"], r["ingresos"]), axis=1)
    out["roa"] = out.apply(lambda r: _safe_div(r["utilidad"], r["activo_total"]), axis=1)
    out["cash_sobre_activo_corr"] = out.apply(lambda r: _safe_div(r.get("efectivo", float("nan")), r["activo_corriente"]), axis=1)
    return out

def _nivel_semaforo(valor, ok, invertido=False, tolerancia=0.1):
    """
    Devuelve 'OK' / 'Atención' / 'Riesgo' según umbral.
    - Si invertido=True (ej. endeudamiento), valores mayores son peores.
    - tolerancia: banda intermedia para 'Atención'.
    """
    if math.isnan(valor):
        return "NA"
    if not invertido:
        if valor >= ok: return "OK"
        if valor >= ok*(1 - tolerancia): return "Atención"
        return "Riesgo"
    else:
        if valor <= ok: return "OK"
        if valor <= ok*(1 + tolerancia): return "Atención"
        return "Riesgo"

def _fmt_pct(x):
    return "NA" if (x is None or (isinstance(x,float) and math.isnan(x))) else f"{x:.1%}"

def _fmt_num(x):
    return "NA" if (x is None or (isinstance(x,float) and math.isnan(x))) else f"{x:,.2f}"

def aplicar_reglas(df_ratios: pd.DataFrame) -> Dict[str, Any]:
    hallazgos: List[Dict[str, Any]] = []

    # Tomamos el último periodo por empresa (si hay varios)
    df_last = df_ratios.sort_values(["codigo_mype","periodo"]).groupby("codigo_mype").tail(1)

    for _, r in df_last.iterrows():
        # Liquidez
        nivel_liq = _nivel_semaforo(r["liquidez"], UMBRALES["liquidez_ok"], invertido=False)
        hallazgos.append({
            "id": f"{r['codigo_mype']}_liq",
            "codigo_mype": r["codigo_mype"],
            "periodo": r["periodo"],
            "titulo": "Liquidez corriente",
            "nivel": nivel_liq,
            "valor": r["liquidez"],
            "mensaje": f"Liquidez = {_fmt_num(r['liquidez'])}. Umbral OK ≥ {UMBRALES['liquidez_ok']:.2f}."
        })

        # Endeudamiento (invertido: más alto es peor)
        nivel_end = _nivel_semaforo(r["endeudamiento"], UMBRALES["endeudamiento_alto"], invertido=True)
        hallazgos.append({
            "id": f"{r['codigo_mype']}_end",
            "codigo_mype": r["codigo_mype"],
            "periodo": r["periodo"],
            "titulo": "Endeudamiento",
            "nivel": nivel_end,
            "valor": r["endeudamiento"],
            "mensaje": f"Endeudamiento = {_fmt_pct(r['endeudamiento'])}. OK ≤ {UMBRALES['endeudamiento_alto']:.0%}."
        })

        # Margen neto
        nivel_mn = _nivel_semaforo(r["margen_neto"], UMBRALES["margen_neto_bajo"], invertido=False)
        hallazgos.append({
            "id": f"{r['codigo_mype']}_mn",
            "codigo_mype": r["codigo_mype"],
            "periodo": r["periodo"],
            "titulo": "Margen neto",
            "nivel": nivel_mn,
            "valor": r["margen_neto"],
            "mensaje": f"Margen neto = {_fmt_pct(r['margen_neto'])}. Umbral ≥ {UMBRALES['margen_neto_bajo']:.0%}."
        })

        # ROA
        nivel_roa = _nivel_semaforo(r["roa"], UMBRALES["roa_bajo"], invertido=False)
        hallazgos.append({
            "id": f"{r['codigo_mype']}_roa",
            "codigo_mype": r["codigo_mype"],
            "periodo": r["periodo"],
            "titulo": "ROA",
            "nivel": nivel_roa,
            "valor": r["roa"],
            "mensaje": f"ROA = {_fmt_pct(r['roa'])}. Umbral ≥ {UMBRALES['roa_bajo']:.0%}."
        })

        # Efectivo mínimo sobre activo corriente
        if "efectivo" in df_ratios.columns:
            val_cash = r["cash_sobre_activo_corr"]
            nivel_cash = _nivel_semaforo(val_cash, UMBRALES["efectivo_min_sobre_activo_corr"], invertido=False)
            hallazgos.append({
                "id": f"{r['codigo_mype']}_cash",
                "codigo_mype": r["codigo_mype"],
                "periodo": r["periodo"],
                "titulo": "Efectivo mínimo",
                "nivel": nivel_cash,
                "valor": val_cash,
                "mensaje": f"Efectivo/Act. Corriente = {_fmt_pct(val_cash)}. Umbral ≥ {UMBRALES['efectivo_min_sobre_activo_corr']:.0%}."
            })

    # Agrega un resumen por nivel
    resumen = (
        pd.DataFrame(hallazgos)
        .groupby(["codigo_mype","nivel"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
        .to_dict(orient="records")
        if hallazgos else []
    )

    return {
        "hallazgos": hallazgos,
        "resumen_niveles": resumen,
        "umbrales": UMBRALES
    }

def calcular_ratios_y_reglas(df_estandar: pd.DataFrame) -> Dict[str, Any]:
    df_ratios = calcular_ratios(df_estandar)
    reglas = aplicar_reglas(df_ratios)
    # Puedes incluir métricas agregadas
    return {
        "df_ratios": df_ratios,
        **reglas
    }
